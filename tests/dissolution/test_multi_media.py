"""Tests for multi-media dissolution comparison (v1.4.0)."""

from pathlib import Path

import pytest

from openpkflow.dissolution import MultiMediaResult, MultiMediaStudy
from openpkflow.dissolution.multi_media import _build_multi_media_figure


def _make_csv(content: str, tmp_path: Path, name: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def _sim_csv(profiles: dict[str, list[float]], times: list[int] = None) -> str:
    if times is None:
        times = [5, 10, 15, 20, 30, 45, 60]
    lines = ["formulation,batch,time,percent_released"]
    for label, means in profiles.items():
        for i, t in enumerate(times):
            lines.append(f"{label},1,{t},{means[i]}")
    return "\n".join(lines)


class TestMultiMediaStudy:
    def test_init_two_media(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        test_sim = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": test_sim}), tmp_path, "ph1.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": test_sim}), tmp_path, "ph6.csv")
        mm = MultiMediaStudy({"pH 1.2": p1, "pH 6.8": p2})
        assert mm.media_names == ["pH 1.2", "pH 6.8"]

    def test_init_three_media(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        p3 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "c.csv")
        mm = MultiMediaStudy({"A": p1, "B": p2, "C": p3})
        assert len(mm.media_names) == 3

    def test_init_missing_reference_raises(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        good = _make_csv(_sim_csv({"reference": ref, "test": ref}), tmp_path, "good.csv")
        bad = _make_csv(_sim_csv({"other": [1, 2, 3, 4, 5, 6, 7]}), tmp_path, "bad.csv")
        with pytest.raises(ValueError, match="Reference formulation"):
            MultiMediaStudy({"Good": good, "Bad": bad})

    def test_init_missing_test_raises(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        good = _make_csv(_sim_csv({"reference": ref, "test": ref}), tmp_path, "good.csv")
        bad = _make_csv(_sim_csv({"reference": ref}), tmp_path, "bad.csv")
        with pytest.raises(ValueError, match="Test formulation"):
            MultiMediaStudy({"Good": good, "Bad": bad})

    def test_init_empty_dict_raises(self):
        with pytest.raises(ValueError, match="At least 2"):
            MultiMediaStudy({})

    def test_init_single_medium_raises(self, tmp_path):
        ref = [1, 2, 3, 4, 5, 6, 7]
        p = _make_csv(_sim_csv({"reference": ref, "test": ref}), tmp_path, "x.csv")
        with pytest.raises(ValueError, match="At least 2"):
            MultiMediaStudy({"X": p})

    def test_run_returns_multi_media_result(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"pH 1.2": p1, "pH 6.8": p2})
        result = mm.run()
        assert isinstance(result, MultiMediaResult)

    def test_run_all_media_in_result(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"pH 1.2": p1, "pH 6.8": p2})
        result = mm.run()
        assert set(result.per_media_results.keys()) == {"pH 1.2", "pH 6.8"}

    def test_run_f2_values_similar(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"pH 1.2": p1, "pH 6.8": p2})
        result = mm.run()
        assert result.f2_summary["pH 1.2"] >= 50
        assert result.f2_summary["pH 6.8"] >= 50
        assert result.overall_pass is True

    def test_run_dissimilar_profile_fails(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        far = [5, 60, 90, 95, 98, 99, 100]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": far}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"Good": p1, "Bad": p2})
        result = mm.run()
        assert result.f2_summary["Good"] >= 50
        assert result.f2_summary["Bad"] < 50
        assert result.overall_pass is False

    def test_result_summary_contains_pass_text(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"pH 1.2": p1, "pH 6.8": p2})
        result = mm.run()
        text = result.summary()
        assert "Multi-Media Dissolution" in text
        assert "PASS" in text

    def test_result_summary_shows_fail_for_bad(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        bad = [5, 60, 90, 95, 98, 99, 100]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": ref}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": bad}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"Good": p1, "Bad": p2})
        result = mm.run()
        text = result.summary()
        assert "FAIL" in text

    def test_result_to_dict_keys(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"pH 1.2": p1, "pH 6.8": p2})
        result = mm.run()
        d = result.to_dict()
        assert "reference_label" in d
        assert "test_label" in d
        assert "media_names" in d
        assert "per_media_results" in d
        assert "f2_summary" in d
        assert "overall_pass" in d

    def test_result_plot_saves_file(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"pH 1.2": p1, "pH 6.8": p2})
        result = mm.run()
        out = tmp_path / "plot.png"
        result.plot(str(out))
        assert out.exists()
        assert out.stat().st_size > 1000

    def test_result_plot_b64_is_png(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"pH 1.2": p1, "pH 6.8": p2})
        result = mm.run()
        b64 = result._plot_b64()
        assert len(b64) > 100
        import base64

        data = base64.b64decode(b64)
        assert data[:4] == b"\x89PNG"

    def test_result_report_html(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"pH 1.2": p1, "pH 6.8": p2})
        result = mm.run()
        out = tmp_path / "report.html"
        html = result.report(str(out), format="html")
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html
        assert out.exists()

    def test_result_report_pdf(self, tmp_path):
        pytest.importorskip("reportlab")
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"pH 1.2": p1, "pH 6.8": p2})
        result = mm.run()
        out = tmp_path / "report.pdf"
        pdf = result.report(str(out), format="pdf")
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"
        assert out.exists()

    def test_result_report_docx(self, tmp_path):
        pytest.importorskip("docx")
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"pH 1.2": p1, "pH 6.8": p2})
        result = mm.run()
        out = tmp_path / "report.docx"
        docx = result.report(str(out), format="docx")
        assert isinstance(docx, bytes)
        assert len(docx) > 2000
        assert out.exists()

    def test_report_unknown_format_raises(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"A": p1, "B": p2})
        result = mm.run()
        with pytest.raises(ValueError, match="Unknown format"):
            result.report("out.txt", format="txt")

    def test_from_csvs_classmethod(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        mm = MultiMediaStudy.from_csvs({"A": p1, "B": p2})
        assert len(mm.media_names) == 2

    def test_run_preserves_media_order(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        csvs = {
            name: _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, f"{name}.csv")
            for name in ["C_third", "A_first", "B_second"]
        }
        mm = MultiMediaStudy(csvs)
        result = mm.run()
        assert result.media_names == list(csvs.keys())

    def test_build_multi_media_figure_two_media(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"pH 1.2": p1, "pH 6.8": p2})
        result = mm.run()
        import matplotlib.pyplot as plt

        fig = _build_multi_media_figure(result.media_names, result.per_media_results)
        assert len(fig.axes) == 2
        plt.close(fig)

    def test_build_multi_media_figure_three_media(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        p3 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "c.csv")
        mm = MultiMediaStudy({"A": p1, "B": p2, "C": p3})
        result = mm.run()
        import matplotlib.pyplot as plt

        fig = _build_multi_media_figure(result.media_names, result.per_media_results)
        assert len(fig.axes) == 3
        plt.close(fig)

    def test_multi_media_plot_shows_both_media_names(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"pH 1.2": p1, "pH 6.8": p2})
        result = mm.run()
        import matplotlib.pyplot as plt

        fig = _build_multi_media_figure(result.media_names, result.per_media_results)
        ax_titles = [ax.get_title() for ax in fig.axes]
        assert any("pH 1.2" in t for t in ax_titles)
        assert any("pH 6.8" in t for t in ax_titles)
        plt.close(fig)

    def test_overall_pass_false_when_any_fails(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        good = [6, 16, 31, 44, 58, 78, 93]
        bad = [5, 60, 90, 95, 98, 99, 100]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": good}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": bad}), tmp_path, "b.csv")
        p3 = _make_csv(_sim_csv({"reference": ref, "test": good}), tmp_path, "c.csv")
        mm = MultiMediaStudy({"G1": p1, "B": p2, "G2": p3})
        result = mm.run()
        assert result.overall_pass is False

    def test_f2_summary_access_by_key(self, tmp_path):
        ref = [5, 15, 30, 45, 60, 80, 95]
        tst = [6, 16, 31, 44, 58, 78, 93]
        p1 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "a.csv")
        p2 = _make_csv(_sim_csv({"reference": ref, "test": tst}), tmp_path, "b.csv")
        mm = MultiMediaStudy({"pH 1.2": p1, "pH 6.8": p2})
        result = mm.run()
        assert isinstance(result.f2_summary["pH 1.2"], float)
        assert isinstance(result.f2_summary["pH 6.8"], float)
