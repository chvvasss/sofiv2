"""Verify all astronomy packages are installed and functional."""
import sys
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def test_numpy():
    import numpy as np
    arr = np.array([101.2871, 279.2347, 88.7929])
    assert arr.mean() > 0
    print(f"  numpy {np.__version__}: OK")


def test_pandas():
    import pandas as pd
    csv_path = TEMPLATE_DIR / "star_catalog_template.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        assert len(df) == 5
        assert "Star_Name" in df.columns
        print(f"  pandas {pd.__version__}: OK (read {len(df)} stars from CSV)")
    else:
        print(f"  pandas {pd.__version__}: OK (CSV template not yet created)")


def test_astropy():
    import astropy
    from astropy.coordinates import SkyCoord
    import astropy.units as u
    coord = SkyCoord(ra=101.2871 * u.degree, dec=-16.7161 * u.degree, frame="icrs")
    assert coord.ra.deg > 0
    print(f"  astropy {astropy.__version__}: OK (SkyCoord works)")


def test_astroquery():
    from astroquery.simbad import Simbad  # noqa: F401
    import astroquery
    print(f"  astroquery {astroquery.__version__}: OK (Simbad module importable)")


def test_matplotlib():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.scatter([1, 2, 3], [4, 5, 6])
    ax.set_title("Test Plot")
    plt.close(fig)
    print(f"  matplotlib {matplotlib.__version__}: OK (scatter plot created)")


def test_seaborn():
    import seaborn as sns
    import pandas as pd
    # Use simple inline data instead of network dataset
    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    plot = sns.scatterplot(data=df, x="x", y="y")
    import matplotlib.pyplot as plt
    plt.close("all")
    print(f"  seaborn {sns.__version__}: OK")


def test_scipy():
    import scipy
    import numpy as np
    magnitudes = np.array([-1.46, 0.03, 0.42, 1.98, 0.85])
    mean, std = np.mean(magnitudes), np.std(magnitudes)
    assert std > 0
    print(f"  scipy {scipy.__version__}: OK (mean mag={mean:.2f}, std={std:.2f})")


def test_fits_io():
    from astropy.table import Table
    fits_path = TEMPLATE_DIR / "star_catalog_template.fits"
    if fits_path.exists():
        t = Table.read(str(fits_path), format="fits")
        assert len(t) == 5
        print(f"  FITS I/O: OK (read {len(t)} rows)")
    else:
        print("  FITS I/O: SKIPPED (template not yet created, run scripts/create_template_fits.py first)")


def test_votable_io():
    from astropy.table import Table
    vot_path = TEMPLATE_DIR / "star_catalog_template.vot"
    if vot_path.exists():
        t = Table.read(str(vot_path), format="votable")
        assert len(t) == 5
        print(f"  VOTable I/O: OK (read {len(t)} rows)")
    else:
        print("  VOTable I/O: SKIPPED (template not yet created, run scripts/create_template_fits.py first)")


def main():
    tests = [
        ("NumPy", test_numpy),
        ("Pandas", test_pandas),
        ("Astropy", test_astropy),
        ("Astroquery", test_astroquery),
        ("Matplotlib", test_matplotlib),
        ("Seaborn", test_seaborn),
        ("SciPy", test_scipy),
        ("FITS I/O", test_fits_io),
        ("VOTable I/O", test_votable_io),
    ]

    print(f"Python {sys.version}")
    print(f"Testing {len(tests)} components...\n")

    passed, failed = 0, 0
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  {name}: FAILED -- {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
