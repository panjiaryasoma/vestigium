"""MODIS -> VIIRS S-NPP detected-pixel count proxy calibration.

Calibrates monthly 25 km EPSG:6933 grid cells from NASA FIRMS type=0 pixel
detections. It DOES NOT recover ignition points, unique fire events, area
burned, missed individual pixels, or intentionality.

Usage:
  python src/pipelines/harmonize.py --input data/processed/geospatial/monthly_equal_area_25km.csv --output data/processed/harmonization
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

EXPECTED = {"MODIS": 1443591, "VIIRS_SNPP": 3350961, "VIIRS_NOAA20": 1203124}
KEY = ["year", "month", "cell_x", "cell_y"]
FEATURES = ["log_modis_count", "log_modis_frp", "log_modis_max_frp",
            "day_fraction", "month_sin", "month_cos",
            "center_longitude", "center_latitude"]

def read_input(path):
    d = pd.read_csv(path)
    need = set(KEY + ["sensor", "detection_count", "frp_sum_mw",
                      "center_longitude", "center_latitude"])
    missing = need.difference(d.columns)
    if missing:
        raise ValueError(f"Missing equal-area source columns: {sorted(missing)}")
    if (d["detection_count"] < 0).any() or (d["frp_sum_mw"] < 0).any():
        raise ValueError("Negative detection count or FRP")
    if d.duplicated(KEY + ["sensor"]).any():
        raise ValueError("Duplicate sensor-grid-month rows; avoid many-to-many joins")
    return d

def make_training_frame(d):
    m = d.loc[d.sensor.eq("MODIS")].copy()
    m = m.rename(columns={"detection_count": "modis_count",
                           "frp_sum_mw": "modis_sum_frp_mw",
                           "max_frp_mw": "modis_max_frp_mw",
                           "daytime_detections": "modis_day",
                           "nighttime_detections": "modis_night"})
    if "modis_max_frp_mw" not in m.columns:
        m["modis_max_frp_mw"] = m["modis_sum_frp_mw"]
    for col in ("modis_day", "modis_night"):
        if col not in m.columns:
            m[col] = 0.
        m[col] = m[col].fillna(0.).astype("float64")
    snpp = d.loc[d.sensor.eq("VIIRS_SNPP"), KEY+["detection_count"]].copy()
    snpp = snpp.rename(columns={"detection_count": "snpp_count"})
    base = m.merge(snpp, on=KEY, how="left", validate="one_to_one", indicator=True)
    base["snpp_reported_this_cell_month"] = base["_merge"].eq("both")
    base = base.drop(columns=["_merge"])
    base.loc[base.year.ge(2012), "snpp_count"] = base.loc[base.year.ge(2012), "snpp_count"].fillna(0.)
    base["log_modis_count"] = np.log1p(base.modis_count)
    base["log_modis_frp"] = np.log1p(base.modis_sum_frp_mw)
    base["log_modis_max_frp"] = np.log1p(base.modis_max_frp_mw)
    base["day_fraction"] = base.modis_day / np.maximum(1,base.modis_day + base.modis_night)
    base["month_sin"] = np.sin(2*np.pi*base.month/12)
    base["month_cos"] = np.cos(2*np.pi*base.month/12)
    return base, snpp

def fitting_splits(base):
    return {
        "train":base.loc[base.year.between(2013, 2021)].copy(),
        "validation":base.loc[base.year.eq(2022)].copy(),
        "test":base.loc[base.year.between(2023, 2025)].copy(),
    }

def calc_scales(train):
    if train.empty:
        raise ValueError("Training set has no MODIS-positive overlap observations")
    global_ratio = float(train.snpp_count.sum()/max(1,train.modis_count.sum()))
    seasonal = {}
    for m in range(1,13):
        a = train.loc[train.month.eq(m)]
        seasonal[m] = float((a.snpp_count.sum() + 1000*global_ratio) / (a.modis_count.sum() + 1000))
    return global_ratio,seasonal

def predict_baselines(frame,global_ratio,seasonal_ratios):
    raw = frame.modis_count.to_numpy(dtype="float64")
    scale = frame.month.map(seasonal_ratios).fillna(global_ratio).to_numpy()
    return {"raw_modis":raw, "global_ratio":raw*global_ratio, "seasonal_ratio":raw*scale}

def fit_ml(train):
    model = HistGradientBoostingRegressor(loss="poisson",max_iter=140,
        max_leaf_nodes=18,max_depth=5,min_samples_leaf=90,
        learning_rate=0.055,l2_regularization=8.0,random_state=42)
    model.fit(train[FEATURES].to_numpy(dtype="float64"),
              train.snpp_count.to_numpy(dtype="float64"))
    return model

def metric(frame, prediction):
    actual = frame.snpp_count.to_numpy(dtype="float64")
    pred = np.clip(np.asarray(prediction,dtype="float64"),0,None)
    if len(actual)!=len(pred):
        raise ValueError("Predictions and truth have different lengths")
    return {
        "n_cells":int(len(actual)),
        "mae":float(mean_absolute_error(actual,pred)),
        "rmse":float(np.sqrt(mean_squared_error(actual,pred))),
        "wape":float(np.abs(actual-pred).sum()/max(1,actual.sum())),
        "volume_bias_pct":float(100*(pred.sum()-actual.sum())/max(1,actual.sum())),
        "spearman_rho":float(pd.Series(actual).corr(pd.Series(pred),method="spearman")),
    }

def all_predictions(frame,global_ratio,seasonal_ratios,model):
    preds = predict_baselines(frame,global_ratio,seasonal_ratios)
    preds["ml_poisson_hgbr"] = np.clip(model.predict(frame[FEATURES].to_numpy(dtype="float64")),0,None)
    return preds

def generate_plots(out, test, cover, regions, annual):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figdir=out/"figures"
    figdir.mkdir(exist_ok=True)
    by_month=test.groupby(["year","month"],as_index=False)[["snpp_count","estimate"]].sum()
    fig,ax=plt.subplots(figsize=(11,4))
    ax.plot(np.arange(len(by_month)),by_month.snpp_count,label="VIIRS S-NPP observed")
    ax.plot(np.arange(len(by_month)),by_month.estimate,label="MODIS-calibrated proxy")
    ax.legend();ax.set_title("Temporal holdout: 2023–2025, MODIS-positive cells only")
    ax.set_xlabel("Months from Jan 2023");ax.set_ylabel("Detected-pixel counts")
    fig.tight_layout();fig.savefig(figdir/"03_temporal_holdout_2023_2025.png",dpi=140);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,4))
    ax.plot(cover.year,100*(1-cover.snpp_pixels_in_modis_positive_share),marker="o")
    ax.set(title="S-NPP detections outside MODIS-positive cells",
           xlabel="UTC year",ylabel="Share (%)")
    fig.tight_layout();fig.savefig(figdir/"05_modis_blind_spot_diagnostic.png",dpi=140);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4))
    ax.bar(regions.region, regions.volume_bias_pct)
    ax.set(title="Holdout spatial bias by longitude band",
           xlabel="Regional longitude bands (not province borders)",ylabel="Volume bias (%)")
    fig.tight_layout();fig.savefig(figdir/"04_regional_bias.png",dpi=140);plt.close(fig)
    a=annual.pivot(index="year",columns="month",values="calendar_display_estimate")
    fig,ax=plt.subplots(figsize=(10,6))
    im=ax.imshow(np.log1p(a.to_numpy(dtype="float64")),aspect="auto")
    ax.set(yticks=np.arange(len(a)),yticklabels=a.index,xticks=np.arange(12),
           xticklabels=np.arange(1,13),title="Hybrid monthly activity proxy (log1p), structural 2012 break",
           xlabel="UTC month",ylabel="UTC year")
    fig.colorbar(im,ax=ax,label="log1p(expected detected pixels)")
    fig.tight_layout();fig.savefig(figdir/"06_harmonized_monthly_heatmap.png",dpi=140);plt.close(fig)

def run(input_csv: Path, output: Path):
    output.mkdir(parents=True,exist_ok=True)
    d=read_input(input_csv)
    sums={k:int(v) for k,v in d.groupby("sensor").detection_count.sum().items()}
    base, snpp=make_training_frame(d)
    splits=fitting_splits(base)
    if any(s.empty for s in splits.values()):
        raise ValueError("Missing 2013–2025 training, validation, or test data")
    train, val, test=[splits[k] for k in ("train","validation","test")]
    ratio,seasonal=calc_scales(train)
    model=fit_ml(train)
    pv=all_predictions(val,ratio,seasonal,model)
    pt=all_predictions(test,ratio,seasonal,model)
    validation={k:metric(val,p) for k,p in pv.items()}
    testing={k:metric(test,p) for k,p in pt.items()}
    selected=min(("global_ratio","seasonal_ratio","ml_poisson_hgbr"),
                 key=lambda m:validation[m]["rmse"])
    preds=all_predictions(base,ratio,seasonal,model)
    calibrated=base.copy()
    calibrated["snpp_equivalent_estimate"]=preds[selected]
    calibrated["method"]=selected
    calibrated["calibration_reference"]="VIIRS_SNPP"
    calibrated["observation_unit"]="satellite_detected_pixel_count_proxy_not_fire_events"
    cut_count=np.quantile(train.modis_count,.995)
    cut_frp=np.quantile(train.modis_sum_frp_mw,.995)
    calibrated["out_of_training_range"]=(calibrated.modis_count>cut_count)|(calibrated.modis_sum_frp_mw>cut_frp)
    calibrated["prediction_role"]=np.select(
        [calibrated.year.le(2011),calibrated.year.eq(2012),
         calibrated.year.between(2013,2021),calibrated.year.eq(2022),
         calibrated.year.ge(2023)],
        ["historical_extrapolation","partial_reference_year","training_overlap",
         "validation_year","untouched_test_overlap"],default="other")
    calibrated=calibrated.rename(columns={"modis_sum_frp_mw":"modis_sum_frp_mw"})
    calibrated.to_csv(output/"calibrated_modis_25km_monthly.csv",index=False)
    raw=d.groupby(["year","month","sensor"],as_index=False).detection_count.sum()
    p=raw.pivot_table(index=["year","month"],columns="sensor",values="detection_count",aggfunc="sum")
    p=p.reindex(columns=["MODIS","VIIRS_SNPP","VIIRS_NOAA20"])
    # Do not replace pre-launch missing observations with zeros.
    index=pd.MultiIndex.from_tuples([(int(y),int(m)) for y,m in pd.period_range(
       "2000-11","2025-12",freq="M").map(lambda p:(p.year,p.month))],names=["year","month"])
    p=p.reindex(index)
    for s,first in (("VIIRS_SNPP",2012),("VIIRS_NOAA20",2018)):
        p.loc[p.index.get_level_values("year")<first,s]=np.nan
    for s,first in (("MODIS",2000),("VIIRS_SNPP",2012),("VIIRS_NOAA20",2018)):
        eligible=p.index.get_level_values("year")>=first
        p.loc[eligible,s]=p.loc[eligible,s].fillna(0)
    proxy=calibrated.groupby(["year","month"],as_index=True).agg(
        modis_reference_equivalent_proxy=("snpp_equivalent_estimate","sum"),
        modis_active_cells=("modis_count","size"),
        model_out_of_domain_cells=("out_of_training_range","sum"))
    p=p.join(proxy,how="left").reset_index()
    p["calendar_display_estimate"]=np.where(p.year<2012,
        p.modis_reference_equivalent_proxy,p.VIIRS_SNPP)
    p["calendar_method"]=np.where(p.year<2012,
        selected+"_historical_proxy","observed_viirs_snpp")
    p["cross_2012_discontinuity_warning"]=True
    p["missing_observation_coverage_unknown"]=True
    p.to_csv(output/"harmonized_calendar_monthly.csv",index=False)
    annual=p.groupby("year",as_index=False).agg({
        "MODIS":"sum","VIIRS_SNPP":"sum","VIIRS_NOAA20":"sum",
        "modis_reference_equivalent_proxy":"sum","modis_active_cells":"sum",
        "model_out_of_domain_cells":"sum","calendar_display_estimate":"sum"})
    # Pandas groupby sum otherwise maps all-NA VIIRS history to a false zero.
    for s,start in (("VIIRS_SNPP",2012),("VIIRS_NOAA20",2018)):
        annual.loc[annual.year<start,s]=np.nan
    annual["incomplete_year"]=annual.year.eq(2000)
    annual["cross_2012_discontinuity_warning"]=True
    annual.to_csv(output/"harmonized_calendar_annual.csv",index=False)
    # Reference coverage is evaluated on S-NPP-positive cells, not all grid cells.
    ref=snpp.copy().rename(columns={"snpp_count":"snpp_total_cell"})
    reference_all=ref.groupby("year").snpp_total_cell.sum().rename("snpp_total")
    intersection=ref.merge(base[KEY],on=KEY,how="inner",validate="one_to_one")
    reference_hit=intersection.groupby("year").snpp_total_cell.sum().rename("snpp_in_modis_positive_cells")
    coverage=pd.concat([reference_all,reference_hit],axis=1).fillna(0).reset_index()
    coverage["snpp_pixels_in_modis_positive_share"]=np.where(coverage.snpp_total>0,
        coverage.snpp_in_modis_positive_cells/coverage.snpp_total,np.nan)
    coverage.to_csv(output/"overlap_coverage_diagnostics.csv",index=False)
    hold=test[KEY+["snpp_count","center_longitude","center_latitude"]].copy()
    hold["estimate"]=pt[selected]
    hold["region"]=pd.cut(hold.center_longitude,[-180,110,125,180],
                           labels=["west_of_110E","110E_to_125E","east_of_125E"])
    hold.to_csv(output/"test_monthly_comparison.csv",index=False)
    regions=hold.groupby("region",observed=True).apply(
        lambda g:pd.Series(metric(g,g.estimate)),include_groups=False).reset_index()
    regions.to_csv(output/"test_regional_diagnostics.csv",index=False)
    evidence={
        "preferred_method":selected,"selection_basis":"2022 validation RMSE; test 2023-2025 untouched",
        "train_years":"2013–2021","validation_year":2022,"test_years":"2023–2025",
        "validation":validation,"test":testing,"source_by_sensor":sums,
        "training_rows":len(train),"validation_rows":len(val),"test_rows":len(test),
        "training_extrapolation_high_tail_quantile":.995,
        "model_hyperparameters":model.get_params(),
        "feature_names":FEATURES,
        "model_lineage":"Reconstructed repository-native pipeline; historical report is not a verified rerun",
        "caveats":["No unique events or burned area estimated",
           "No overpass/clear-sky denominators",
           "Reference available only for MODIS-positive grid-months",
           "Structural discontinuity before/after 2012",
           "Sensor sensitivity and regional/temporal bias remain",
           "Model uncertainty intervals not calibrated"]
    }
    (output/"evaluation.json").write_text(json.dumps(evidence,indent=2,default=str),encoding="utf8")
    try:
        import joblib
        joblib.dump(model,output/"poisson_model.joblib")
    except ImportError:
        pass
    try:
        generate_plots(output,hold,coverage,regions,p)
    except ImportError:
        print("Matplotlib unavailable: numerical outputs preserved; figures omitted.")
    print(json.dumps({k:evidence[k] for k in ("preferred_method","train_years","validation_year","test_years","test")},indent=2))
    return evidence

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    run(args.input,args.output)
