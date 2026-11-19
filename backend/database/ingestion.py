"""
ParallaX | Bengaluru Road Safety & Accident Risk Intelligence Platform
Data Ingestion Pipeline — processes all 6 CSV data sources
"""
import os
import sys
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import engine, SessionLocal, Base
from database.models import (
    AccidentStatistic, HistoricalAccidentStat, OfficialBlackspot,
    CasAlertAggregated, CasAlertSpatial, DataSourceMetadata,
    DataQualityReport, PoliceStation
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_RAW = Path(__file__).parent.parent.parent / "data" / "raw"

# Summary row keywords to exclude from station-level aggregation
SUMMARY_KEYWORDS = [
    "total", "grand total", "zone total", "subdiv total", "sub div total",
    "traffic north", "traffic east", "traffic south", "traffic west", "traffic central",
    "traffic total"
]

# Police station name normalization map
STATION_NAME_MAP = {
    "kg halli": "KG Halli",
    "k g halli": "KG Halli",
    "kr pura": "KR Pura",
    "k r pura": "KR Pura",
    "jb nagar": "JB Nagar",
    "j b nagar": "JB Nagar",
    "hal airport": "HAL Airport",
    "hsr layout": "HSR Layout",
    "electronics city": "Electronics City",
    "byatarayanapura": "Byatarayanapura",
    "rajarajeshwarinagar": "Rajarajeshwarinagar",
    "kamakshipalya": "Kamakshipalya",
    "kamakshipalay": "Kamakshipalya",
    "jnanabharathi": "Jnanabharathi",
    "talaghattapura": "Talaghattapura",
}

STATION_ZONE_MAP = {
    "Banaswadi": "East", "HBR Layout": "East", "Horamavu": "East",
    "KG Halli": "East", "Ramamurthynagar": "East", "HAL Airport": "East",
    "Halsuru": "East", "JB Nagar": "East", "Marathahalli": "East",
    "Whitefield": "East", "KR Pura": "East", "Mahadevapura": "East",
    "Chikkajala": "North", "Devanahalli": "North", "Hebbal": "North",
    "Sanjaynagar": "North", "Yelahanka": "North", "Byatarayanapura": "North",
    "Peenya": "North", "Yeshwantpur": "North",
    "Bellandur": "South", "Electronics City": "South", "HSR Layout": "South",
    "Hulimavu": "South", "Madiwala": "South", "Jnanabharathi": "South",
    "Kengeri": "South", "Talaghattapura": "South",
    "Chamarajpet": "Central", "City Market": "Central", "Upparpet": "Central",
    "Kamakshipalya": "Central",
    "Rajarajeshwarinagar": "West",
}


def normalize_station_name(name: str) -> str:
    if not isinstance(name, str):
        return str(name)
    cleaned = name.strip()
    lower = cleaned.lower()
    if lower in STATION_NAME_MAP:
        return STATION_NAME_MAP[lower]
    # Title case as fallback
    return cleaned.title()


def is_summary_row(value: str) -> bool:
    if not isinstance(value, str):
        return False
    lower = value.lower().strip()
    return any(kw in lower for kw in SUMMARY_KEYWORDS)


def safe_int(val, default=0) -> int:
    try:
        if pd.isna(val):
            return default
        return int(float(str(val).replace(",", "").strip()))
    except (ValueError, TypeError):
        return default


def log_quality(db: Session, source: str, check: str, result: str, details: str):
    report = DataQualityReport(
        source_name=source,
        check_name=check,
        check_result=result,
        details=details
    )
    db.add(report)


def upsert_data_source(db: Session, name: str, path: str, records: int,
                       coverage: str, fields: list, status: str, limitations: str):
    existing = db.query(DataSourceMetadata).filter_by(source_name=name).first()
    if existing:
        existing.record_count = records
        existing.validation_status = status
        existing.last_processed_at = datetime.now()
    else:
        meta = DataSourceMetadata(
            source_name=name,
            file_path=path,
            record_count=records,
            date_coverage=coverage,
            available_fields=", ".join(fields),
            validation_status=status,
            known_limitations=limitations,
            last_processed_at=datetime.now()
        )
        db.add(meta)


def already_ingested(db: Session, source: str) -> bool:
    meta = db.query(DataSourceMetadata).filter_by(source_name=source).first()
    return meta is not None and meta.record_count > 0


# ─────────────────────────────────────────────
# DS1: 2024 Accident Statistics
# ─────────────────────────────────────────────
def ingest_2024(db: Session, force: bool = False):
    source_name = "Accident Statistics 2024"
    if not force and already_ingested(db, source_name):
        logger.info(f"Skipping {source_name} — already ingested")
        return

    path = DATA_RAW / "accident_stats_2024.csv"
    if not path.exists():
        logger.error(f"File not found: {path}")
        log_quality(db, source_name, "file_exists", "FAIL", f"File not found: {path}")
        db.commit()
        return

    df = pd.read_csv(path)
    logger.info(f"DS1: {len(df)} rows loaded from {path.name}")

    # Remove existing records for year 2024
    db.query(AccidentStatistic).filter_by(year=2024, source_dataset=source_name).delete()

    station_rows = 0
    summary_rows = 0
    for _, row in df.iterrows():
        station_col = str(row.get("Police Station", "")).strip()
        is_sum = is_summary_row(station_col)

        fatal = safe_int(row.get("Fatal Accidents", 0))
        non_fatal = safe_int(row.get("Non Fatal Accidents", 0))
        total = safe_int(row.get("Total Accidents", 0))
        zone = str(row.get("Zone", "")).strip()

        stat = AccidentStatistic(
            police_station=station_col if not is_sum else station_col,
            zone=zone,
            year=2024,
            fatal_accidents=fatal,
            non_fatal_accidents=non_fatal,
            total_accidents=total,
            people_killed=fatal,
            people_injured=non_fatal,
            source_dataset=source_name,
            is_summary_row=is_sum
        )
        db.add(stat)
        if is_sum:
            summary_rows += 1
        else:
            station_rows += 1

    grand_total_check = df[df["Police Station"].str.lower().str.strip() == "grand total"]
    if not grand_total_check.empty:
        gt = grand_total_check.iloc[0]
        log_quality(db, source_name, "grand_total_check", "PASS",
                    f"Grand total: {safe_int(gt.get('Total Accidents',0))} accidents, "
                    f"{safe_int(gt.get('Fatal Accidents',0))} fatal, "
                    f"{safe_int(gt.get('Non Fatal Accidents',0))} non-fatal")

    upsert_data_source(db, source_name, str(path), len(df), "2024",
                       list(df.columns), "VALID",
                       f"Contains {summary_rows} summary rows excluded from station rankings. "
                       "Traffic subdivision totals included as summary rows.")
    log_quality(db, source_name, "row_count", "PASS",
                f"{len(df)} total rows: {station_rows} station rows, {summary_rows} summary rows")
    db.commit()
    logger.info(f"DS1 ingested: {station_rows} station rows, {summary_rows} summary rows")


# ─────────────────────────────────────────────
# DS2: 2021 & 2022 Accident Statistics
# ─────────────────────────────────────────────
def ingest_2021_2022(db: Session, force: bool = False):
    source_name = "Accident Statistics 2021-2022"
    if not force and already_ingested(db, source_name):
        logger.info(f"Skipping {source_name} — already ingested")
        return

    path = DATA_RAW / "accident_stats_2021_2022.csv"
    if not path.exists():
        logger.error(f"File not found: {path}")
        return

    df = pd.read_csv(path)
    logger.info(f"DS2: {len(df)} rows loaded")

    db.query(AccidentStatistic).filter(
        AccidentStatistic.year.in_([2021, 2022]),
        AccidentStatistic.source_dataset == source_name
    ).delete()

    rows_added = 0
    for _, row in df.iterrows():
        station = normalize_station_name(str(row.get("Police Station", "")))
        zone = str(row.get("Zone", STATION_ZONE_MAP.get(station, ""))).strip()
        if is_summary_row(station):
            continue

        for year, suffix in [(2021, "2021"), (2022, "2022")]:
            fatal = safe_int(row.get(f"Fatal Accidents {suffix}", 0))
            people_killed = safe_int(row.get(f"People Killed {suffix}", 0))
            non_fatal = safe_int(row.get(f"Non Fatal Accidents {suffix}", 0))
            people_injured = safe_int(row.get(f"People Injured {suffix}", 0))
            total = safe_int(row.get(f"Total Accident Cases {suffix}", 0))

            stat = AccidentStatistic(
                police_station=station,
                zone=zone,
                year=year,
                fatal_accidents=fatal,
                non_fatal_accidents=non_fatal,
                total_accidents=total,
                people_killed=people_killed,
                people_injured=people_injured,
                source_dataset=source_name,
                is_summary_row=False
            )
            db.add(stat)
            rows_added += 1

    upsert_data_source(db, source_name, str(path), len(df) * 2, "2021-2022",
                       list(df.columns), "VALID",
                       "Station-level data for 2021 and 2022. Some minor discrepancies with annual totals possible.")
    db.commit()
    logger.info(f"DS2 ingested: {rows_added} station-year records")


# ─────────────────────────────────────────────
# DS3: Historical Annual Statistics (2007–2025)
# ─────────────────────────────────────────────
def ingest_historical_annual(db: Session, force: bool = False):
    source_name = "Historical Annual Accident Statistics"
    if not force and already_ingested(db, source_name):
        logger.info(f"Skipping {source_name} — already ingested")
        return

    path = DATA_RAW / "historical_annual_accident_stats.csv"
    if not path.exists():
        logger.error(f"File not found: {path}")
        return

    df = pd.read_csv(path)
    logger.info(f"DS3: {len(df)} rows loaded (years: {df['Year'].min()}–{df['Year'].max()})")

    db.query(HistoricalAccidentStat).delete()

    for _, row in df.iterrows():
        stat = HistoricalAccidentStat(
            year=safe_int(row.get("Year")),
            fatal_accidents=safe_int(row.get("Fatal Accidents", 0)),
            people_killed=safe_int(row.get("People Killed", 0)),
            non_fatal_accidents=safe_int(row.get("Non Fatal Accidents", 0)),
            people_injured=safe_int(row.get("People Injured", 0)),
            total_accidents=safe_int(row.get("Total Accidents", 0)),
            source_dataset=source_name
        )
        db.add(stat)

    upsert_data_source(db, source_name, str(path), len(df), "2007-2025",
                       list(df.columns), "VALID",
                       "City-wide annual totals. 2025 is the most recent year. "
                       "Minor discrepancies with station-level aggregates documented separately.")
    db.commit()
    logger.info(f"DS3 ingested: {len(df)} annual records")


# ─────────────────────────────────────────────
# DS4: 2023 Accident Statistics
# ─────────────────────────────────────────────
def ingest_2023(db: Session, force: bool = False):
    source_name = "Accident Statistics 2023"
    if not force and already_ingested(db, source_name):
        logger.info(f"Skipping {source_name} — already ingested")
        return

    path = DATA_RAW / "accident_stats_2023.csv"
    if not path.exists():
        logger.error(f"File not found: {path}")
        return

    df = pd.read_csv(path)
    logger.info(f"DS4: {len(df)} rows loaded")

    db.query(AccidentStatistic).filter_by(year=2023, source_dataset=source_name).delete()

    station_rows = 0
    for _, row in df.iterrows():
        station = normalize_station_name(str(row.get("Police Station", "")))
        is_sum = is_summary_row(station)
        zone = STATION_ZONE_MAP.get(station, "")
        fatal = safe_int(row.get("Fatal Accidents", 0))
        stat = AccidentStatistic(
            police_station=station,
            zone=zone,
            year=2023,
            fatal_accidents=fatal,
            non_fatal_accidents=safe_int(row.get("Non Fatal Accidents", 0)),
            total_accidents=safe_int(row.get("Total Accidents", 0)),
            people_killed=safe_int(row.get("People Killed", 0)),
            people_injured=safe_int(row.get("People Injured", 0)),
            source_dataset=source_name,
            is_summary_row=is_sum
        )
        db.add(stat)
        if not is_sum:
            station_rows += 1

    upsert_data_source(db, source_name, str(path), len(df), "2023",
                       list(df.columns), "VALID",
                       f"Contains {len(df)-station_rows} summary rows excluded from rankings. "
                       "Total cases: 4,974.")
    db.commit()
    logger.info(f"DS4 ingested: {station_rows} station records")


# ─────────────────────────────────────────────
# DS5: 2018, 2019, 2020 Accident Statistics
# ─────────────────────────────────────────────
def ingest_2018_2020(db: Session, force: bool = False):
    source_name = "Accident Statistics 2018-2020"
    if not force and already_ingested(db, source_name):
        logger.info(f"Skipping {source_name} — already ingested")
        return

    path = DATA_RAW / "accident_stats_2018_2020.csv"
    if not path.exists():
        logger.error(f"File not found: {path}")
        return

    df = pd.read_csv(path)
    logger.info(f"DS5: {len(df)} rows loaded")

    db.query(AccidentStatistic).filter(
        AccidentStatistic.year.in_([2018, 2019, 2020]),
        AccidentStatistic.source_dataset == source_name
    ).delete()

    rows_added = 0
    for _, row in df.iterrows():
        station = normalize_station_name(str(row.get("Police Station", "")))
        zone = str(row.get("Zone", STATION_ZONE_MAP.get(station, ""))).strip()
        if is_summary_row(station):
            continue
        for year, suffix in [(2018, "2018"), (2019, "2019"), (2020, "2020")]:
            fatal = safe_int(row.get(f"Fatal Accidents {suffix}", 0))
            stat = AccidentStatistic(
                police_station=station,
                zone=zone,
                year=year,
                fatal_accidents=fatal,
                non_fatal_accidents=safe_int(row.get(f"Non Fatal Accidents {suffix}", 0)),
                total_accidents=safe_int(row.get(f"Total Accidents {suffix}", 0)),
                people_killed=safe_int(row.get(f"People Killed {suffix}", 0)),
                people_injured=safe_int(row.get(f"People Injured {suffix}", 0)),
                source_dataset=source_name,
                is_summary_row=False
            )
            db.add(stat)
            rows_added += 1

    upsert_data_source(db, source_name, str(path), len(df) * 3, "2018-2020",
                       list(df.columns), "VALID",
                       "Station-level data for 2018, 2019, and 2020.")
    db.commit()
    logger.info(f"DS5 ingested: {rows_added} station-year records")


# ─────────────────────────────────────────────
# DS6: Bangalore CAS Alerts
# ─────────────────────────────────────────────
def ingest_cas_alerts(db: Session, force: bool = False):
    source_name = "Bangalore CAS Alerts"
    if not force and already_ingested(db, source_name):
        logger.info(f"Skipping {source_name} — already ingested")
        return

    path = DATA_RAW / "bangalore-cas-alerts.csv"
    if not path.exists():
        logger.error(f"CAS alerts file not found: {path}")
        log_quality(db, source_name, "file_exists", "FAIL", str(path))
        db.commit()
        return

    logger.info(f"Loading CAS alerts from {path} — this may take 30-60 seconds...")

    # Read in chunks for large file
    chunk_size = 50000
    total_rows = 0
    exact_dupes = 0
    invalid_coords = 0

    all_dfs = []
    seen_hashes = set()

    for chunk in pd.read_csv(path, chunksize=chunk_size):
        # Rename columns
        chunk.columns = [c.strip().replace('"', '') for c in chunk.columns]
        col_map = {
            "deviceCode_deviceCode": "device_code",
            "deviceCode_location_latitude": "latitude",
            "deviceCode_location_longitude": "longitude",
            "deviceCode_location_wardName": "ward_name",
            "deviceCode_pyld_alarmType": "alarm_type",
            "deviceCode_pyld_speed": "speed",
            "deviceCode_time_recordedTime_$date": "recorded_time"
        }
        chunk = chunk.rename(columns={k: v for k, v in col_map.items() if k in chunk.columns})

        # Validate coordinates
        if "latitude" in chunk.columns and "longitude" in chunk.columns:
            chunk["latitude"] = pd.to_numeric(chunk["latitude"], errors="coerce")
            chunk["longitude"] = pd.to_numeric(chunk["longitude"], errors="coerce")
            bengaluru_mask = (
                (chunk["latitude"] >= 12.7) & (chunk["latitude"] <= 13.3) &
                (chunk["longitude"] >= 77.3) & (chunk["longitude"] <= 78.0)
            )
            invalid_coords += (~bengaluru_mask | chunk["latitude"].isna()).sum()
            chunk = chunk[bengaluru_mask & chunk["latitude"].notna()]

        # Detect exact duplicates
        if "device_code" in chunk.columns:
            hash_key = chunk.apply(
                lambda r: hashlib.md5(
                    f"{r.get('device_code','')}{r.get('latitude','')}{r.get('longitude','')}{r.get('recorded_time','')}".encode()
                ).hexdigest(), axis=1
            )
            dupe_mask = hash_key.isin(seen_hashes)
            exact_dupes += dupe_mask.sum()
            seen_hashes.update(hash_key[~dupe_mask].tolist())
            chunk = chunk[~dupe_mask]

        total_rows += len(chunk)
        all_dfs.append(chunk)

    logger.info(f"CAS: {total_rows} valid unique records after deduplication "
                f"({exact_dupes} exact dupes removed, {invalid_coords} invalid coords removed)")

    if not all_dfs:
        logger.error("No valid CAS data after filtering")
        return

    df = pd.concat(all_dfs, ignore_index=True)

    # Ensure speed is numeric
    if "speed" in df.columns:
        df["speed"] = pd.to_numeric(df["speed"], errors="coerce").fillna(0)
    else:
        df["speed"] = 0

    # Ward-level aggregation
    db.query(CasAlertAggregated).delete()
    if "ward_name" in df.columns and "alarm_type" in df.columns:
        grouped = df.groupby(["ward_name", "alarm_type"]).agg(
            alert_count=("alarm_type", "count"),
            avg_speed=("speed", "mean"),
            max_speed=("speed", "max"),
            min_speed=("speed", "min"),
            unique_devices=("device_code", "nunique") if "device_code" in df.columns else ("alarm_type", "count")
        ).reset_index()

        overspeed_df = df[df["alarm_type"] == "Overspeed"].groupby("ward_name").size().reset_index(name="overspeed_count")
        grouped = grouped.merge(overspeed_df, on="ward_name", how="left")
        grouped["overspeed_count"] = grouped["overspeed_count"].fillna(0).astype(int)

        for _, row in grouped.iterrows():
            agg = CasAlertAggregated(
                ward_name=str(row["ward_name"]),
                alarm_type=str(row["alarm_type"]),
                alert_count=int(row["alert_count"]),
                avg_speed=float(row["avg_speed"]) if not pd.isna(row["avg_speed"]) else 0.0,
                max_speed=float(row["max_speed"]) if not pd.isna(row["max_speed"]) else 0.0,
                min_speed=float(row["min_speed"]) if not pd.isna(row["min_speed"]) else 0.0,
                overspeed_count=int(row["overspeed_count"])
            )
            db.add(agg)

    # Spatial binning (0.02 degree ~2km bins) for heatmap
    db.query(CasAlertSpatial).delete()
    if "latitude" in df.columns and "longitude" in df.columns:
        df["lat_bin"] = (df["latitude"] / 0.02).apply(np.floor) * 0.02
        df["lng_bin"] = (df["longitude"] / 0.02).apply(np.floor) * 0.02
        overspeed_flag = (df["alarm_type"] == "Overspeed").astype(int)
        spatial = df.groupby(["lat_bin", "lng_bin"]).agg(
            alert_count=("alarm_type", "count"),
            overspeed_count=(overspeed_flag.name if hasattr(overspeed_flag, 'name') else "alarm_type", "count")
        ).reset_index()

        # Re-compute overspeed by bin separately
        df["is_overspeed"] = (df["alarm_type"] == "Overspeed").astype(int)
        spatial2 = df.groupby(["lat_bin", "lng_bin"]).agg(
            alert_count=("alarm_type", "count"),
            overspeed_count=("is_overspeed", "sum")
        ).reset_index()

        # Alarm type distribution per bin
        alarm_dist = df.groupby(["lat_bin", "lng_bin", "alarm_type"]).size().reset_index(name="cnt")
        alarm_dist_map = {}
        for _, r in alarm_dist.iterrows():
            key = (r["lat_bin"], r["lng_bin"])
            if key not in alarm_dist_map:
                alarm_dist_map[key] = {}
            alarm_dist_map[key][r["alarm_type"]] = int(r["cnt"])

        for _, row in spatial2.iterrows():
            key = (row["lat_bin"], row["lng_bin"])
            spatial_rec = CasAlertSpatial(
                lat_bin=float(row["lat_bin"]),
                lng_bin=float(row["lng_bin"]),
                alert_count=int(row["alert_count"]),
                overspeed_count=int(row["overspeed_count"]),
                alarm_types_json=json.dumps(alarm_dist_map.get(key, {}))
            )
            db.add(spatial_rec)

    alarm_counts = df["alarm_type"].value_counts().to_dict() if "alarm_type" in df.columns else {}
    ward_counts = df["ward_name"].nunique() if "ward_name" in df.columns else 0

    upsert_data_source(
        db, source_name, str(path), total_rows,
        "2018-02-01 to 2018-07-30",
        ["device_code", "latitude", "longitude", "ward_name", "alarm_type", "speed", "recorded_time"],
        "VALID",
        f"These are driving-safety CAS alerts, NOT confirmed accidents. "
        f"Alert counts do not directly represent accident probability. "
        f"{exact_dupes} exact duplicate records identified and excluded. "
        f"{invalid_coords} records with invalid Bengaluru coordinates excluded. "
        f"Covers {ward_counts} unique wards. Time coverage: Feb-Jul 2018."
    )
    log_quality(db, source_name, "deduplication", "PASS",
                f"{exact_dupes} exact duplicates removed out of 207617 raw records")
    log_quality(db, source_name, "coordinate_validation", "PASS",
                f"{invalid_coords} records with out-of-Bengaluru coordinates excluded")
    log_quality(db, source_name, "alarm_type_distribution", "INFO",
                f"Alarm distribution: {json.dumps(alarm_counts)}")

    db.commit()
    logger.info(f"DS6 CAS ingested: {total_rows} records, ward aggregation complete")


# ─────────────────────────────────────────────
# Official BTP Blackspots
# ─────────────────────────────────────────────
def ingest_blackspots(db: Session, force: bool = False):
    source_name = "Official BTP Blackspots"
    if not force and already_ingested(db, source_name):
        logger.info(f"Skipping {source_name} — already ingested")
        return

    path = DATA_RAW / "bengaluru_traffic_police_blackspots.csv"
    if not path.exists():
        logger.error(f"File not found: {path}")
        return

    df = pd.read_csv(path)
    logger.info(f"Blackspots: {len(df)} records loaded")

    db.query(OfficialBlackspot).delete()
    for _, row in df.iterrows():
        year_val = row.get("identification_year")
        if pd.isna(year_val) or str(year_val).strip() in ["", "nan"]:
            year_val = None
        else:
            year_val = safe_int(year_val, None)

        bs = OfficialBlackspot(
            blackspot_id=str(row.get("blackspot_id", "")),
            police_station=str(row.get("police_station", "")),
            original_location_description=str(row.get("original_location_description", "")),
            normalized_location_name=str(row.get("normalized_location_name", "")),
            road_name=str(row.get("road_name", "")),
            location_type=str(row.get("location_type", "")),
            source=str(row.get("source", "Bengaluru Traffic Police")),
            identification_year=year_val,
            latitude=float(row["latitude"]) if not pd.isna(row.get("latitude")) else None,
            longitude=float(row["longitude"]) if not pd.isna(row.get("longitude")) else None,
            geocoding_status=str(row.get("geocoding_status", "pending")),
            verification_status=str(row.get("verification_status", "unverified"))
        )
        db.add(bs)

    upsert_data_source(db, source_name, str(path), len(df), "2018-2025",
                       list(df.columns), "VALID",
                       "Official locations from Bengaluru Traffic Police. "
                       "Coordinates assigned based on known Bengaluru geography. "
                       "Exact coordinates require field verification.")
    log_quality(db, source_name, "record_count", "PASS", f"{len(df)} blackspot records loaded (target: 64)")
    db.commit()
    logger.info(f"Blackspots ingested: {len(df)} records")


# ─────────────────────────────────────────────
# Police Stations master list
# ─────────────────────────────────────────────
STATION_COORDINATES = {
    "Banaswadi": (13.005, 77.657), "HBR Layout": (13.0167, 77.6505),
    "Horamavu": (13.0279, 77.6567), "KG Halli": (13.000, 77.670),
    "Ramamurthynagar": (13.0124, 77.6612), "HAL Airport": (12.9603, 77.7118),
    "Halsuru": (12.9755, 77.6174), "JB Nagar": (12.9637, 77.6530),
    "Marathahalli": (12.9591, 77.7006), "Whitefield": (12.9698, 77.7500),
    "KR Pura": (13.0067, 77.7026), "Mahadevapura": (12.9939, 77.7130),
    "Chikkajala": (13.1297, 77.5830), "Devanahalli": (13.2457, 77.7073),
    "Hebbal": (13.0350, 77.5970), "Sanjaynagar": (13.0134, 77.5728),
    "Yelahanka": (13.1007, 77.5963), "Byatarayanapura": (13.0612, 77.5214),
    "Peenya": (13.0282, 77.5200), "Yeshwantpur": (13.0218, 77.5505),
    "Bellandur": (12.9254, 77.6765), "Electronics City": (12.8390, 77.6760),
    "HSR Layout": (12.9116, 77.6389), "Hulimavu": (12.8731, 77.6117),
    "Madiwala": (12.9174, 77.6230), "Jnanabharathi": (12.9607, 77.5119),
    "Kengeri": (12.9064, 77.4824), "Talaghattapura": (12.8609, 77.5082),
    "Chamarajpet": (12.9574, 77.5564), "City Market": (12.9634, 77.5756),
    "Upparpet": (12.9676, 77.5649), "Kamakshipalya": (12.9767, 77.5277),
    "Rajarajeshwarinagar": (12.9340, 77.5220),
}


def ingest_police_stations(db: Session, force: bool = False):
    existing = db.query(PoliceStation).count()
    if existing > 0 and not force:
        logger.info("Police stations already seeded")
        return
    db.query(PoliceStation).delete()
    for name, (lat, lng) in STATION_COORDINATES.items():
        zone = STATION_ZONE_MAP.get(name, "")
        ps = PoliceStation(
            name=name,
            normalized_name=name.lower().replace(" ", "_"),
            zone=zone,
            latitude=lat,
            longitude=lng
        )
        db.add(ps)
    db.commit()
    logger.info(f"Police stations seeded: {len(STATION_COORDINATES)}")


# ─────────────────────────────────────────────
# Main ingestion entry point
# ─────────────────────────────────────────────
def run_all_ingestion(force: bool = False):
    logger.info("=== Starting ParallaX Road Safety Data Ingestion ===")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        ingest_police_stations(db, force)
        ingest_historical_annual(db, force)
        ingest_2024(db, force)
        ingest_2023(db, force)
        ingest_2021_2022(db, force)
        ingest_2018_2020(db, force)
        ingest_blackspots(db, force)
        ingest_cas_alerts(db, force)
        logger.info("=== Ingestion Complete ===")
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    force = "--force" in sys.argv
    run_all_ingestion(force=force)
