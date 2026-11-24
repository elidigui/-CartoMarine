# -*- coding: utf-8 -*-
"""
Cartes météo marine — Manche + Atlantique français, 9 octobre 2026
Source : Copernicus Marine (compte gratuit requis)

Prérequis :
    pip install copernicusmarine xarray matplotlib numpy

Première utilisation : authentifiez-vous une fois (identifiants créés sur
data.marine.copernicus.eu) :
    copernicusmarine login

Produit 3 cartes PNG : carte_temperature.png, carte_courants.png, carte_salinite.png
Les variables sont dans 3 datasets séparés (nouveau découpage Copernicus) :
    cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m  (température)
    cmems_mod_glo_phy-so_anfc_0.083deg_P1D-m      (salinité)
    cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m     (courants uo, vo)
Chacun est téléchargé dans un fichier local NetCDF, avec relances
automatiques en cas d'erreur réseau.
"""

import os
import time

import copernicusmarine
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr

DATE = "2026-10-09"
# Zone : Manche + Atlantique français
LAT_MIN, LAT_MAX = 43.0, 51.5
LON_MIN, LON_MAX = -6.0, 2.5

SUBSET_KW = dict(
    minimum_longitude=LON_MIN,
    maximum_longitude=LON_MAX,
    minimum_latitude=LAT_MIN,
    maximum_latitude=LAT_MAX,
    start_datetime=f"{DATE}T00:00:00",
    end_datetime=f"{DATE}T23:00:00",
    minimum_depth=0,
    maximum_depth=1,  # surface (le 1er niveau est à ~0,49 m)
)

DATASETS = [
    ("cmems_mod_glo_phy-thetao_anfc_0.083deg_P1D-m", ["thetao"], "data_temperature.nc"),
    ("cmems_mod_glo_phy-so_anfc_0.083deg_P1D-m",     ["so"],     "data_salinite.nc"),
    ("cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m",    ["uo", "vo"], "data_courants.nc"),
]


def download_one(dataset_id: str, variables: list, nc_file: str) -> None:
    """Télécharge un dataset dans un fichier local NetCDF (avec relances)."""
    if os.path.exists(nc_file):
        print(f"Fichier {nc_file} déjà présent, réutilisation.")
        return
    for tentative in range(1, 4):
        try:
            print(f"Téléchargement de {dataset_id} (tentative {tentative}/3)...")
            copernicusmarine.subset(
                dataset_id=dataset_id,
                variables=variables,
                output_filename=nc_file,
                overwrite=True,
                **SUBSET_KW,
            )
            return
        except Exception as exc:  # timeout réseau, coupure, etc.
            print(f"Échec : {exc}")
            if tentative == 3:
                raise
            print("Nouvelle tentative dans 30 secondes...")
            time.sleep(30)


def main():
    for dataset_id, variables, nc_file in DATASETS:
        download_one(dataset_id, variables, nc_file)

    # Fusion des trois fichiers sur les coordonnées communes
    ds = xr.merge([
        xr.open_dataset("data_temperature.nc"),
        xr.open_dataset("data_salinite.nc"),
        xr.open_dataset("data_courants.nc"),
    ]).isel(time=0)

    lon = ds["longitude"].values
    lat = ds["latitude"].values
    temp = ds["thetao"].isel(depth=0).values        # °C
    sal = ds["so"].isel(depth=0).values             # PSU
    uo = ds["uo"].isel(depth=0).values              # m/s, vers l'est
    vo = ds["vo"].isel(depth=0).values              # m/s, vers le nord
    speed = np.sqrt(uo**2 + vo**2)

    LON, LAT = np.meshgrid(lon, lat)

    # --- Carte 1 : température ---
    fig, ax = plt.subplots(figsize=(9, 8), constrained_layout=True)
    pc = ax.pcolormesh(LON, LAT, temp, cmap="turbo",
                       vmin=10, vmax=22, shading="auto")
    fig.colorbar(pc, ax=ax, label="Température (°C)", shrink=0.85)
    ax.set_title(f"Température de surface de la mer — {DATE}")
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    fig.savefig("carte_temperature.png", dpi=150)
    plt.close(fig)

    # --- Carte 2 : courants (vitesse + flèches) ---
    step = max(1, len(lon) // 30)  # sous-échantillonnage des flèches
    fig, ax = plt.subplots(figsize=(9, 8), constrained_layout=True)
    pc = ax.pcolormesh(LON, LAT, speed * 100, cmap="viridis",
                       vmin=0, vmax=80, shading="auto")
    q = ax.quiver(LON[::step, ::step], LAT[::step, ::step],
                  uo[::step, ::step], vo[::step, ::step],
                  color="white", scale=15, width=0.003)
    ax.quiverkey(q, 0.9, 1.03, 0.5, "0,5 m/s", labelpos="E")
    fig.colorbar(pc, ax=ax, label="Vitesse du courant (cm/s)", shrink=0.85)
    ax.set_title(f"Courants de surface — {DATE}")
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    fig.savefig("carte_courants.png", dpi=150)
    plt.close(fig)

    # --- Carte 3 : salinité ---
    fig, ax = plt.subplots(figsize=(9, 8), constrained_layout=True)
    pc = ax.pcolormesh(LON, LAT, sal, cmap="cividis",
                       vmin=34, vmax=36, shading="auto")
    fig.colorbar(pc, ax=ax, label="Salinité (PSU)", shrink=0.85)
    ax.set_title(f"Salinité de surface — {DATE}")
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    fig.savefig("carte_salinite.png", dpi=150)
    plt.close(fig)

    # Résumé chiffré
    print(f"\nZone : {LAT_MIN}-{LAT_MAX} deg N, {LON_MIN}-{LON_MAX} deg E - {DATE}")
    print(f"Température : moyenne {np.nanmean(temp):.1f} °C "
          f"(min {np.nanmin(temp):.1f}, max {np.nanmax(temp):.1f})")
    print(f"Salinité    : moyenne {np.nanmean(sal):.2f} PSU")
    print(f"Courant max : {np.nanmax(speed):.2f} m/s")
    print("\nCartes enregistrées : carte_temperature.png, carte_courants.png, carte_salinite.png")


if __name__ == "__main__":
    main()