"# -*- coding: utf-8 -*-
"""
Cartes météo marine — Manche + Atlantique français, 9 octobre 2026
Source : Copernicus Marine (compte gratuit requis)

Prérequis :
    pip install copernicusmarine xarray matplotlib numpy

Première utilisation : authentifiez-vous une fois (identifiants créés sur
data.marine.copernicus.eu) :
    copernicusmarine login

Le script télécharge les données puis produit 3 cartes PNG :
    carte_temperature.png, carte_courants.png, carte_salinite.png
"""

import copernicusmarine
import numpy as np
import matplotlib.pyplot as plt

DATE = "2026-10-09"
# Zone : Manche + Atlantique français
LAT_MIN, LAT_MAX = 43.0, 51.5
LON_MIN, LON_MAX = -6.0, 2.5

# Produit analyse/prévision physique global (couvre 2026 ; GLORYS12
# GLOBAL_MULTIYEAR_PHY_001_030 convient pour des dates plus anciennes)
DATASET = "cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m"

def main():
    print("Téléchargement des données Copernicus Marine...")
    ds = copernicusmarine.open_dataset(
        dataset_id=DATASET,
        minimum_longitude=LON_MIN,
        maximum_longitude=LON_MAX,
        minimum_latitude=LAT_MIN,
        maximum_latitude=LAT_MAX,
        start_datetime=f"{DATE}T00:00:00",
        end_datetime=f"{DATE}T23:00:00",
        variables=["thetao", "so", "uo", "vo"],
        minimum_depth=0,
        maximum_depth=0,  # surface uniquement
    )
    # On prend le premier pas de temps du jour
    ds = ds.isel(time=0)

    lon = ds["longitude"].values
    lat = ds["latitude"].values
    temp = ds["thetao"].isel(depth=0).values        # °C
    sal = ds["so"].isel(depth=0).values             # PSU
    uo = ds["uo"].isel(depth=0).values              # m/s, vers l'est
    vo = ds["vo"].isel(depth=0).values              # m/s, vers le nord
    speed = np.sqrt(uo**2 + vo**2)
    # Orientation (direction VERS laquelle le courant va), en degrés depuis le Nord
    direction = (np.degrees(np.arctan2(uo, vo)) + 360) % 360

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
    pc = ax.pcolormesh(LON, LAT, sal, cmap="cmo.haline" if _try_cmo() else "cividis",
                       vmin=34, vmax=36, shading="auto")
    fig.colorbar(pc, ax=ax, label="Salinité (PSU)", shrink=0.85)
    ax.set_title(f"Salinité de surface — {DATE}")
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°N)")
    fig.savefig("carte_salinite.png", dpi=150)
    plt.close(fig)

    # Résumé chiffré
    print(f"\
Zone : {LAT_MIN}-{LAT_MAX}°N, {LON_MIN}-{LON_MAX}°E — {DATE}")
    print(f"Température : moyenne {np.nanmean(temp):.1f} °C "
          f"(min {np.nanmin(temp):.1f}, max {np.nanmax(temp):.1f})")
    print(f"Salinité    : moyenne {np.nanmean(sal):.2f} PSU")
    print(f"Courant max : {np.nanmax(speed):.2f} m/s")
    print("\
Cartes enregistrées : carte_temperature.png, carte_courants.png, carte_salinite.png")

def _try_cmo():
    try:
        import cmocean  # optionnel : pip install cmocean
        return True
    except ImportError:
        return False

if __name__ == "__main__":
    main()
"