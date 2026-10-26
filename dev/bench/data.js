window.BENCHMARK_DATA = {
  "lastUpdate": 1793004736292,
  "repoUrl": "https://github.com/priyamthakar/openpkflow",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "priyamthakar1@gmail.com",
            "name": "Priyam Thakar",
            "username": "priyamthakar"
          },
          "committer": {
            "email": "priyamthakar1@gmail.com",
            "name": "Priyam Thakar",
            "username": "priyamthakar"
          },
          "distinct": true,
          "id": "180e758e52d6ec1c77d87ca1ddd5170db9973974",
          "message": "docs(handoff): record that Render did not redeploy non-API merges\n\nOn 2026-10-26, /health stayed at e909e5c (#66) through five later main\nmerges that touched only .github/, webapp/ and docs. 2d3c17b was the\nCI-green head for about 1.5 h. The docs said documentation-only merges\nredeploy and that git_sha follows the latest main; state what was\nobserved instead, without asserting a cause, and add a Render dashboard\ncheck to the owner's next objectives.\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>",
          "timestamp": "2026-10-26T14:19:56+05:30",
          "tree_id": "d4becbc9574c910160f99d9fb4eb2eda3e9d84db",
          "url": "https://github.com/priyamthakar/openpkflow/commit/180e758e52d6ec1c77d87ca1ddd5170db9973974"
        },
        "date": 1793004735319,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmark.py::test_f2_benchmark",
            "value": 494431.44422147854,
            "unit": "iter/sec",
            "range": "stddev: 3.333108662867245e-7",
            "extra": "mean: 2.022525087526703 usec\nrounds: 52277"
          },
          {
            "name": "tests/test_benchmark.py::test_f1_benchmark",
            "value": 535116.1418550097,
            "unit": "iter/sec",
            "range": "stddev: 2.921195630948927e-7",
            "extra": "mean: 1.8687531953968808 usec\nrounds: 105541"
          },
          {
            "name": "tests/test_benchmark.py::test_bootstrap_f2_benchmark",
            "value": 130.5164121998927,
            "unit": "iter/sec",
            "range": "stddev: 0.0010361732307372176",
            "extra": "mean: 7.661871661538227 msec\nrounds: 130"
          },
          {
            "name": "tests/test_benchmark.py::test_fit_models_benchmark",
            "value": 242.07522345011873,
            "unit": "iter/sec",
            "range": "stddev: 0.000653372613126408",
            "extra": "mean: 4.1309473383840825 msec\nrounds: 198"
          },
          {
            "name": "tests/test_benchmark.py::test_auc_linear_benchmark",
            "value": 262217.45603054593,
            "unit": "iter/sec",
            "range": "stddev: 0.00000487991933506566",
            "extra": "mean: 3.8136286391380034 usec\nrounds: 62446"
          },
          {
            "name": "tests/test_benchmark.py::test_auc_linear_up_log_down_benchmark",
            "value": 150139.3694301923,
            "unit": "iter/sec",
            "range": "stddev: 5.705093029551688e-7",
            "extra": "mean: 6.660478219638138 usec\nrounds: 23232"
          },
          {
            "name": "tests/test_benchmark.py::test_lambda_z_benchmark",
            "value": 5526.075664783263,
            "unit": "iter/sec",
            "range": "stddev: 0.000006909300527803485",
            "extra": "mean: 180.9602438802692 usec\nrounds: 1103"
          },
          {
            "name": "tests/test_benchmark.py::test_sparse_nca_benchmark",
            "value": 768.8050392200042,
            "unit": "iter/sec",
            "range": "stddev: 0.000058865834991632965",
            "extra": "mean: 1.3007198821362516 msec\nrounds: 543"
          },
          {
            "name": "tests/test_benchmark.py::test_c_1cmt_oral_benchmark",
            "value": 105038.51038858756,
            "unit": "iter/sec",
            "range": "stddev: 0.000003415077857811369",
            "extra": "mean: 9.520317798686625 usec\nrounds: 34289"
          },
          {
            "name": "tests/test_benchmark.py::test_c_1cmt_iv_bolus_benchmark",
            "value": 125549.317902914,
            "unit": "iter/sec",
            "range": "stddev: 0.000004685088003642321",
            "extra": "mean: 7.964997474325505 usec\nrounds: 25735"
          },
          {
            "name": "tests/test_benchmark.py::test_c_2cmt_iv_bolus_benchmark",
            "value": 91399.1256552684,
            "unit": "iter/sec",
            "range": "stddev: 0.000007587095757251734",
            "extra": "mean: 10.941023700507994 usec\nrounds: 27721"
          },
          {
            "name": "tests/test_benchmark.py::test_simulate_1cmt_oral_repeated_benchmark",
            "value": 14866.705080739965,
            "unit": "iter/sec",
            "range": "stddev: 0.0000026665426220887322",
            "extra": "mean: 67.26440018612563 usec\nrounds: 5375"
          },
          {
            "name": "tests/test_benchmark.py::test_simulate_2cmt_iv_repeated_benchmark",
            "value": 16596.076553282794,
            "unit": "iter/sec",
            "range": "stddev: 0.0000021206753388360986",
            "extra": "mean: 60.25520530647315 usec\nrounds: 7199"
          },
          {
            "name": "tests/test_benchmark.py::test_wagner_nelson_benchmark",
            "value": 89121.37919106304,
            "unit": "iter/sec",
            "range": "stddev: 8.346796088133154e-7",
            "extra": "mean: 11.22065220575355 usec\nrounds: 15052"
          },
          {
            "name": "tests/test_benchmark.py::test_convolution_predict_benchmark",
            "value": 30851.921436702578,
            "unit": "iter/sec",
            "range": "stddev: 0.0000018931203243693826",
            "extra": "mean: 32.412892080373425 usec\nrounds: 6023"
          },
          {
            "name": "tests/test_benchmark.py::test_map_pk_oral_benchmark",
            "value": 131.952669981916,
            "unit": "iter/sec",
            "range": "stddev: 0.0002657435205385736",
            "extra": "mean: 7.578474919355926 msec\nrounds: 124"
          },
          {
            "name": "tests/test_benchmark.py::test_map_pk_iv_benchmark",
            "value": 125.18876939734307,
            "unit": "iter/sec",
            "range": "stddev: 0.00026432638489102655",
            "extra": "mean: 7.9879369756087995 msec\nrounds: 123"
          },
          {
            "name": "tests/test_benchmark.py::test_tost_benchmark",
            "value": 22453.17198340089,
            "unit": "iter/sec",
            "range": "stddev: 0.000018026962928381956",
            "extra": "mean: 44.537137146558926 usec\nrounds: 4703"
          }
        ]
      }
    ]
  }
}