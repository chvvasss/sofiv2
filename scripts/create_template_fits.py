"""Create template FITS and VOTable files for the star catalog."""
from pathlib import Path

import numpy as np
from astropy.table import Table

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def create_template():
    data = {
        "Star_Name": ["Sirius", "Vega", "Betelgeuse", "Polaris", "Aldebaran"],
        "Catalog": ["Hipparcos", "Tycho-2", "Gaia DR3", "SDSS", "Pan-STARRS"],
        "RA_orig": np.array([101.2871, 279.2347, 88.7929, 37.9546, 68.9802]),
        "Dec_orig": np.array([-16.7161, 38.7837, 7.4071, 89.2641, 16.5093]),
        "RA_J2000": np.array([101.2871, 279.2347, 88.7929, 37.9546, 68.9802]),
        "Dec_J2000": np.array([-16.7161, 38.7837, 7.4071, 89.2641, 16.5093]),
        "Magnitude": np.array([-1.46, 0.03, 0.42, 1.98, 0.85]),
        "Band": ["V", "V", "G", "r", "g"],
        "Epoch": ["J1991.25", "J2000.0", "J2016.0", "J2000.0", "J2012.0"],
        "Notes": [
            "Brightest star",
            "A0V standard",
            "Variable red supergiant",
            "Cepheid variable",
            "K5III giant",
        ],
        "Reference": [
            "HIP 32349",
            "TYC 3105-2070-1",
            "Gaia DR3 3322773986249472",
            "SDSS J023149.04+891551.0",
            "PSO J068.9802+16.5093",
        ],
    }

    table = Table(data)

    fits_path = TEMPLATE_DIR / "star_catalog_template.fits"
    table.write(str(fits_path), format="fits", overwrite=True)
    print(f"FITS template created: {fits_path}")

    vot_path = TEMPLATE_DIR / "star_catalog_template.vot"
    table.write(str(vot_path), format="votable", overwrite=True)
    print(f"VOTable template created: {vot_path}")


if __name__ == "__main__":
    create_template()
