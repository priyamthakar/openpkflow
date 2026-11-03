window.BENCHMARK_DATA = {
  "lastUpdate": 1793670737842,
  "repoUrl": "https://github.com/priyamthakar/openpkflow",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "134533542+priyamthakar@users.noreply.github.com",
            "name": "priyamthakar",
            "username": "priyamthakar"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "3c69c4cd46af306172bb93683c65ea8bad78fc19",
          "message": "docs(validation): state the PowerTOST tolerances the tests assert (#76)\n\n* chore(repo): tidy layout for the Python package\n\nRemove stray files (docs/openfit planning notes for another project,\nSESSION_SUMMARY_*.md, root demo.ipynb, old conda-forge meta.yaml,\ncommitted generated example reports, probe_* scratch scripts).\n\nMove internal maintainer notes to dev/ and split scripts/ into\ncrossval/ (reference cross-validation) and ops/ (release and deployment\nchecks), with a scripts/README.md index. Cross-validation R scripts now\ndefault to repo-relative dataset paths instead of D:/ paths, and every\nreference to a moved file is updated.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_011UaeeECPMayTq7oGto3pT4\n\n* build(pkg): polish package metadata and slim the sdist\n\nUse an SPDX license expression with license-files, align the summary\nwith the project positioning, add OS-independent and medical-science\nclassifiers and a Changelog URL, and stop shipping agent instructions\nand codecov.yml in the sdist. Record the layout cleanup in CHANGELOG.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_011UaeeECPMayTq7oGto3pT4\n\n* docs(repo): state facts plainly in the cleanup notes\n\nscripts/README.md now gives the script counts by reference type (10 R\npackage, 6 base R, 1 WinNonlin export, 1 published table), corrects the\nreplicate-BE row (base-R summaries, PowerTOST only when installed), and\nsays what each ops check compares.\n\nThe CHANGELOG entry lists what moved and what was removed, and corrects\nthe removed conda-forge recipe version (2.5.0, not 2.7.0).\n\nThe FOCE-I test comment no longer claims the fixture fills\n_OPENPKFLOW_REFERENCE; the dict is empty and unused.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_011UaeeECPMayTq7oGto3pT4\n\n* docs: correct stated outputs and plain the wording in README and docs\n\nFix example outputs that did not match the code: the f1/f2 example in\ndocs/index.md and the dissolution tutorial printed 2.07 and 89.63, not\n1.33 and 72.80; the pct_bias example now rounds before printing 2.4; the\nsimulation comment matches the summary output.\n\nRemove claims the code does not support: the Levy-plot 0.05-0.95 cutoff\nis an OpenPKFlow choice, not an FDA convention; the theory guide covers\nseven named modules, not \"every module\"; report formats are stated per\nresult type.\n\nRefresh the README size table (measured 2026-11-02, with the method and\ntest command stated) and the web-app status, which still said v2.8.0.\nDrop the stale \"for agents\" release section from docs/positioning.md and\npoint user-facing footnotes at VALIDATION.md instead of dev/HANDOFF.md.\n\nReplace em dashes, arrows and \"->\" headings, colon and hook headings,\nand promotional phrases (\"clean\", \"faster, cleaner, and more\nreproducible\", \"regulatory test traceability matrix\") with plain\nstatements. Changelogs are left as historical records.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_011UaeeECPMayTq7oGto3pT4\n\n* docs(readme): replace the competitor comparison with a capabilities table\n\nThe table marked what PKNCA, WinNonlin and Pharmpy can and cannot do,\nwhich this repository cannot support. It now lists OpenPKFlow\ncapabilities by area with the release whose CHANGELOG entry added each\none, and a dash where the CHANGELOG shows no single release. Rows that\nonly made sense as comparisons (open source, Python-native API,\nregulatory citations) are dropped. The pop PK estimation row now gives\nv2.1.0, with 2-cmt and full Omega in v2.2.0; it said v2.3.0.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_011UaeeECPMayTq7oGto3pT4\n\n* feat(api): add to_dict/to_dataframe to every result and lazy subpackages\n\nFifteen public result classes had no to_dict(), including four of the\nfive bioequivalence results, so getting a BE decision into pandas or\nJSON meant reading attributes one by one. Every exported result class\nnow has to_dict(), built on a shared helper (openpkflow._export) that\nturns NumPy values and DataFrames into built-in types. Seven tabular\nresults gain to_dataframe().\n\nimport openpkflow exposed nothing; subpackages are now attributes that\nimport on first access (PEP 562), so `import openpkflow as opf;\nopf.nca.NCAStudy` works and `import openpkflow` stays at ~10 ms.\n\nNo calculation code changed. tests/test_export.py builds each result\nthrough the public API and checks JSON round-trips, DataFrame shapes\nand the lazy import.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_011UaeeECPMayTq7oGto3pT4\n\n* fix(lint): satisfy the pinned pre-commit ruff on the export changes\n\n#73 merged with the pre-commit job red. Its ruff (v0.11.0) reports F401\nfor the TYPE_CHECKING subpackage imports in openpkflow/__init__.py,\nbecause __all__ was built at runtime and ruff cannot read it, and UP038\nfor two isinstance tuples in _export.py. __all__ is now a literal list,\na test keeps it equal to the lazy-import set, and the isinstance calls\nuse X | Y. Reproduced with ruff 0.11.0 locally; it now passes.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_011UaeeECPMayTq7oGto3pT4\n\n* release: v2.10.0\n\nBump the version in pyproject.toml, __init__.py and CITATION.cff, date\nthe CHANGELOG section (copied to docs/changelog.md), and update the\ncurrent-release text in README.md and docs/index.md.\n\nv2.10.0 adds to_dict() to every public result object, to_dataframe() to\nthe table-shaped ones, and attribute access to subpackages after\n`import openpkflow`. No pharmacometric calculation changed.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_011UaeeECPMayTq7oGto3pT4\n\n* docs(validation): state the PowerTOST tolerances the tests assert\n\nVALIDATION.md said the six power scenarios match PowerTOST 1.5-7 within\n1e-5; tests/validation/test_be_power_reference.py asserts abs=1e-8. The\nsample-size row omitted that achieved power is also checked to 1e-8.\nThe low-power row (1e-9) and the v2.9.0 CHANGELOG entry already match\ntheir tests and are unchanged.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_011UaeeECPMayTq7oGto3pT4\n\n---------\n\nCo-authored-by: Claude <noreply@anthropic.com>",
          "timestamp": "2026-11-03T07:18:46+05:30",
          "tree_id": "f8fb6fd51fbc7a4975eb791284bc660fcb92047e",
          "url": "https://github.com/priyamthakar/openpkflow/commit/3c69c4cd46af306172bb93683c65ea8bad78fc19"
        },
        "date": 1793670737409,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmark.py::test_f2_benchmark",
            "value": 285047.3160406249,
            "unit": "iter/sec",
            "range": "stddev: 7.610328444439231e-7",
            "extra": "mean: 3.5081894960115325 usec\nrounds: 50133"
          },
          {
            "name": "tests/test_benchmark.py::test_f1_benchmark",
            "value": 296146.5317117993,
            "unit": "iter/sec",
            "range": "stddev: 6.347938444682891e-7",
            "extra": "mean: 3.376706774919009 usec\nrounds: 79277"
          },
          {
            "name": "tests/test_benchmark.py::test_bootstrap_f2_benchmark",
            "value": 51.85107103571914,
            "unit": "iter/sec",
            "range": "stddev: 0.00020626395590677503",
            "extra": "mean: 19.286004705883904 msec\nrounds: 51"
          },
          {
            "name": "tests/test_benchmark.py::test_fit_models_benchmark",
            "value": 97.02025613791703,
            "unit": "iter/sec",
            "range": "stddev: 0.0003167401310028869",
            "extra": "mean: 10.307125952939886 msec\nrounds: 85"
          },
          {
            "name": "tests/test_benchmark.py::test_auc_linear_benchmark",
            "value": 153719.46873899866,
            "unit": "iter/sec",
            "range": "stddev: 9.260395384260657e-7",
            "extra": "mean: 6.505356856898243 usec\nrounds: 52699"
          },
          {
            "name": "tests/test_benchmark.py::test_auc_linear_up_log_down_benchmark",
            "value": 83136.14091852732,
            "unit": "iter/sec",
            "range": "stddev: 0.000001304186053377495",
            "extra": "mean: 12.028463060126777 usec\nrounds: 29724"
          },
          {
            "name": "tests/test_benchmark.py::test_lambda_z_benchmark",
            "value": 1716.6629589062964,
            "unit": "iter/sec",
            "range": "stddev: 0.000024267610117144652",
            "extra": "mean: 582.5255300184903 usec\nrounds: 1066"
          },
          {
            "name": "tests/test_benchmark.py::test_sparse_nca_benchmark",
            "value": 303.6075226363856,
            "unit": "iter/sec",
            "range": "stddev: 0.00011204561832675797",
            "extra": "mean: 3.2937260293041093 msec\nrounds: 273"
          },
          {
            "name": "tests/test_benchmark.py::test_c_1cmt_oral_benchmark",
            "value": 46176.91172030317,
            "unit": "iter/sec",
            "range": "stddev: 0.000002891654973768367",
            "extra": "mean: 21.655844073269147 usec\nrounds: 20112"
          },
          {
            "name": "tests/test_benchmark.py::test_c_1cmt_iv_bolus_benchmark",
            "value": 61161.191184618474,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022417287812951022",
            "extra": "mean: 16.350237472998916 usec\nrounds: 13850"
          },
          {
            "name": "tests/test_benchmark.py::test_c_2cmt_iv_bolus_benchmark",
            "value": 43061.736014874106,
            "unit": "iter/sec",
            "range": "stddev: 0.0000028532950041530507",
            "extra": "mean: 23.222472954982273 usec\nrounds: 16528"
          },
          {
            "name": "tests/test_benchmark.py::test_simulate_1cmt_oral_repeated_benchmark",
            "value": 6795.002451862061,
            "unit": "iter/sec",
            "range": "stddev: 0.000010608016990121513",
            "extra": "mean: 147.16698148151013 usec\nrounds: 3294"
          },
          {
            "name": "tests/test_benchmark.py::test_simulate_2cmt_iv_repeated_benchmark",
            "value": 7569.472857316674,
            "unit": "iter/sec",
            "range": "stddev: 0.000009786867650679357",
            "extra": "mean: 132.1095958529526 usec\nrounds: 5112"
          },
          {
            "name": "tests/test_benchmark.py::test_wagner_nelson_benchmark",
            "value": 43629.695316872756,
            "unit": "iter/sec",
            "range": "stddev: 0.000003340771396996918",
            "extra": "mean: 22.920169227339837 usec\nrounds: 12953"
          },
          {
            "name": "tests/test_benchmark.py::test_convolution_predict_benchmark",
            "value": 12290.301911711875,
            "unit": "iter/sec",
            "range": "stddev: 0.000008428733540860071",
            "extra": "mean: 81.3649662297607 usec\nrounds: 4501"
          },
          {
            "name": "tests/test_benchmark.py::test_map_pk_oral_benchmark",
            "value": 55.77409433046822,
            "unit": "iter/sec",
            "range": "stddev: 0.00016241657795496462",
            "extra": "mean: 17.929470877193985 msec\nrounds: 57"
          },
          {
            "name": "tests/test_benchmark.py::test_map_pk_iv_benchmark",
            "value": 51.92140192337946,
            "unit": "iter/sec",
            "range": "stddev: 0.00042530610976860645",
            "extra": "mean: 19.259880568627604 msec\nrounds: 51"
          },
          {
            "name": "tests/test_benchmark.py::test_tost_benchmark",
            "value": 9171.306727848994,
            "unit": "iter/sec",
            "range": "stddev: 0.000018192333397232695",
            "extra": "mean: 109.03571646594972 usec\nrounds: 3407"
          }
        ]
      }
    ]
  }
}