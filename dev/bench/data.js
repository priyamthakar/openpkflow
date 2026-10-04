window.BENCHMARK_DATA = {
  "lastUpdate": 1791082765356,
  "repoUrl": "https://github.com/priyamthakar/openpkflow",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "49699333+dependabot[bot]@users.noreply.github.com",
            "name": "dependabot[bot]",
            "username": "dependabot[bot]"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "fe622c18c9cb3bbcef7ed9b89bf951f79efeb42b",
          "message": "deps(deps): update uvicorn requirement from >=0.52.4 to >=0.54.0 (#60)\n\nUpdates the requirements on [uvicorn](https://github.com/Kludex/uvicorn) to permit the latest version.\n- [Release notes](https://github.com/Kludex/uvicorn/releases)\n- [Changelog](https://github.com/Kludex/uvicorn/blob/main/docs/release-notes.md)\n- [Commits](https://github.com/Kludex/uvicorn/compare/0.52.4...0.54.0)\n\n---\nupdated-dependencies:\n- dependency-name: uvicorn\n  dependency-version: 0.54.0\n  dependency-type: direct:production\n...\n\nSigned-off-by: dependabot[bot] <support@github.com>\nCo-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>",
          "timestamp": "2026-10-04T08:27:21+05:30",
          "tree_id": "718193a94822c4792c7b53c091fbe7fdc90bacf2",
          "url": "https://github.com/priyamthakar/openpkflow/commit/fe622c18c9cb3bbcef7ed9b89bf951f79efeb42b"
        },
        "date": 1791082764587,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmark.py::test_f2_benchmark",
            "value": 521813.2536821295,
            "unit": "iter/sec",
            "range": "stddev: 2.8147302890017486e-7",
            "extra": "mean: 1.9163944053616648 usec\nrounds: 55197"
          },
          {
            "name": "tests/test_benchmark.py::test_f1_benchmark",
            "value": 543169.3278294316,
            "unit": "iter/sec",
            "range": "stddev: 0.0000014123989324835",
            "extra": "mean: 1.8410465185803426 usec\nrounds: 127519"
          },
          {
            "name": "tests/test_benchmark.py::test_bootstrap_f2_benchmark",
            "value": 142.8536019083029,
            "unit": "iter/sec",
            "range": "stddev: 0.00016118085632275438",
            "extra": "mean: 7.000173510793907 msec\nrounds: 139"
          },
          {
            "name": "tests/test_benchmark.py::test_fit_models_benchmark",
            "value": 252.76930647146847,
            "unit": "iter/sec",
            "range": "stddev: 0.00026237095077761007",
            "extra": "mean: 3.956176538834931 msec\nrounds: 206"
          },
          {
            "name": "tests/test_benchmark.py::test_auc_linear_benchmark",
            "value": 294453.9670544684,
            "unit": "iter/sec",
            "range": "stddev: 8.500504646671889e-7",
            "extra": "mean: 3.3961165814927496 usec\nrounds: 75415"
          },
          {
            "name": "tests/test_benchmark.py::test_auc_linear_up_log_down_benchmark",
            "value": 151895.39693897948,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017497565341764755",
            "extra": "mean: 6.583477973343243 usec\nrounds: 41450"
          },
          {
            "name": "tests/test_benchmark.py::test_lambda_z_benchmark",
            "value": 5895.554941072803,
            "unit": "iter/sec",
            "range": "stddev: 0.00000914943039600907",
            "extra": "mean: 169.61931658600267 usec\nrounds: 1254"
          },
          {
            "name": "tests/test_benchmark.py::test_sparse_nca_benchmark",
            "value": 807.3698576632665,
            "unit": "iter/sec",
            "range": "stddev: 0.00004022198881068185",
            "extra": "mean: 1.238589712643291 msec\nrounds: 609"
          },
          {
            "name": "tests/test_benchmark.py::test_c_1cmt_oral_benchmark",
            "value": 113949.73908140066,
            "unit": "iter/sec",
            "range": "stddev: 6.559776806833354e-7",
            "extra": "mean: 8.775798944880814 usec\nrounds: 40755"
          },
          {
            "name": "tests/test_benchmark.py::test_c_1cmt_iv_bolus_benchmark",
            "value": 139382.7291036002,
            "unit": "iter/sec",
            "range": "stddev: 6.380927207341928e-7",
            "extra": "mean: 7.17449002779047 usec\nrounds: 44675"
          },
          {
            "name": "tests/test_benchmark.py::test_c_2cmt_iv_bolus_benchmark",
            "value": 101849.43684066988,
            "unit": "iter/sec",
            "range": "stddev: 7.642400550885296e-7",
            "extra": "mean: 9.818414622796288 usec\nrounds: 36737"
          },
          {
            "name": "tests/test_benchmark.py::test_simulate_1cmt_oral_repeated_benchmark",
            "value": 14845.66626902229,
            "unit": "iter/sec",
            "range": "stddev: 0.000002419491268535573",
            "extra": "mean: 67.35972518031407 usec\nrounds: 4996"
          },
          {
            "name": "tests/test_benchmark.py::test_simulate_2cmt_iv_repeated_benchmark",
            "value": 17173.962758853242,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022426426489780194",
            "extra": "mean: 58.22767954265513 usec\nrounds: 10407"
          },
          {
            "name": "tests/test_benchmark.py::test_wagner_nelson_benchmark",
            "value": 93326.49754799418,
            "unit": "iter/sec",
            "range": "stddev: 9.013589858369396e-7",
            "extra": "mean: 10.715070492019043 usec\nrounds: 19449"
          },
          {
            "name": "tests/test_benchmark.py::test_convolution_predict_benchmark",
            "value": 31649.157000908643,
            "unit": "iter/sec",
            "range": "stddev: 0.0000017269638288011888",
            "extra": "mean: 31.59641819121091 usec\nrounds: 7652"
          },
          {
            "name": "tests/test_benchmark.py::test_map_pk_oral_benchmark",
            "value": 137.91374446236765,
            "unit": "iter/sec",
            "range": "stddev: 0.00018805905853001828",
            "extra": "mean: 7.250908920632409 msec\nrounds: 126"
          },
          {
            "name": "tests/test_benchmark.py::test_map_pk_iv_benchmark",
            "value": 129.17636928258992,
            "unit": "iter/sec",
            "range": "stddev: 0.0006694217151935103",
            "extra": "mean: 7.741353976379158 msec\nrounds: 127"
          },
          {
            "name": "tests/test_benchmark.py::test_tost_benchmark",
            "value": 23607.468707241835,
            "unit": "iter/sec",
            "range": "stddev: 0.00001837589984526126",
            "extra": "mean: 42.359475825260326 usec\nrounds: 4819"
          }
        ]
      }
    ]
  }
}