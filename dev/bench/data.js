window.BENCHMARK_DATA = {
  "lastUpdate": 1788715971243,
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
          "id": "0c2a2738446f52806c84228ec4e42842834a00da",
          "message": "docs(handoff): correct pre-commit fix description",
          "timestamp": "2026-09-06T23:00:35+05:30",
          "tree_id": "50b258c7c39c9f6a088459be7e4fea9cac447b32",
          "url": "https://github.com/priyamthakar/openpkflow/commit/0c2a2738446f52806c84228ec4e42842834a00da"
        },
        "date": 1788715970435,
        "tool": "pytest",
        "benches": [
          {
            "name": "tests/test_benchmark.py::test_f2_benchmark",
            "value": 274054.7231194716,
            "unit": "iter/sec",
            "range": "stddev: 7.647537541390267e-7",
            "extra": "mean: 3.648906279072079 usec\nrounds: 46105"
          },
          {
            "name": "tests/test_benchmark.py::test_f1_benchmark",
            "value": 289319.93420447316,
            "unit": "iter/sec",
            "range": "stddev: 7.368839780080517e-7",
            "extra": "mean: 3.456381264393842 usec\nrounds: 74767"
          },
          {
            "name": "tests/test_benchmark.py::test_bootstrap_f2_benchmark",
            "value": 50.89000952421973,
            "unit": "iter/sec",
            "range": "stddev: 0.00013535024741840245",
            "extra": "mean: 19.650222299999314 msec\nrounds: 50"
          },
          {
            "name": "tests/test_benchmark.py::test_fit_models_benchmark",
            "value": 98.2044981953791,
            "unit": "iter/sec",
            "range": "stddev: 0.0002583096412696953",
            "extra": "mean: 10.182832949367425 msec\nrounds: 79"
          },
          {
            "name": "tests/test_benchmark.py::test_auc_linear_benchmark",
            "value": 147931.44103035834,
            "unit": "iter/sec",
            "range": "stddev: 9.770650642697256e-7",
            "extra": "mean: 6.759888182220715 usec\nrounds: 53462"
          },
          {
            "name": "tests/test_benchmark.py::test_auc_linear_up_log_down_benchmark",
            "value": 104335.46932154764,
            "unit": "iter/sec",
            "range": "stddev: 0.000001181688393918168",
            "extra": "mean: 9.584468316504493 usec\nrounds: 39437"
          },
          {
            "name": "tests/test_benchmark.py::test_lambda_z_benchmark",
            "value": 1727.2200006601508,
            "unit": "iter/sec",
            "range": "stddev: 0.00002095868853263023",
            "extra": "mean: 578.9650418694757 usec\nrounds: 1027"
          },
          {
            "name": "tests/test_benchmark.py::test_sparse_nca_benchmark",
            "value": 310.78086057667366,
            "unit": "iter/sec",
            "range": "stddev: 0.00013195279998759512",
            "extra": "mean: 3.217701367273507 msec\nrounds: 275"
          },
          {
            "name": "tests/test_benchmark.py::test_c_1cmt_oral_benchmark",
            "value": 45019.183109901154,
            "unit": "iter/sec",
            "range": "stddev: 0.000002673557805859369",
            "extra": "mean: 22.21275311812728 usec\nrounds: 19645"
          },
          {
            "name": "tests/test_benchmark.py::test_c_1cmt_iv_bolus_benchmark",
            "value": 59784.85259903419,
            "unit": "iter/sec",
            "range": "stddev: 0.0000022784879725197088",
            "extra": "mean: 16.72664490296251 usec\nrounds: 21856"
          },
          {
            "name": "tests/test_benchmark.py::test_c_2cmt_iv_bolus_benchmark",
            "value": 42034.929343012365,
            "unit": "iter/sec",
            "range": "stddev: 0.0000027390718523467703",
            "extra": "mean: 23.78973904868081 usec\nrounds: 16482"
          },
          {
            "name": "tests/test_benchmark.py::test_simulate_1cmt_oral_repeated_benchmark",
            "value": 6648.798995052067,
            "unit": "iter/sec",
            "range": "stddev: 0.000012027463746943008",
            "extra": "mean: 150.40310298810124 usec\nrounds: 3447"
          },
          {
            "name": "tests/test_benchmark.py::test_simulate_2cmt_iv_repeated_benchmark",
            "value": 7461.862977948226,
            "unit": "iter/sec",
            "range": "stddev: 0.000010064097274886197",
            "extra": "mean: 134.0147900002002 usec\nrounds: 5100"
          },
          {
            "name": "tests/test_benchmark.py::test_wagner_nelson_benchmark",
            "value": 43448.06768779549,
            "unit": "iter/sec",
            "range": "stddev: 0.0000034519151732301522",
            "extra": "mean: 23.015983292644766 usec\nrounds: 13228"
          },
          {
            "name": "tests/test_benchmark.py::test_convolution_predict_benchmark",
            "value": 11966.522337499397,
            "unit": "iter/sec",
            "range": "stddev: 0.000010377246944714507",
            "extra": "mean: 83.56646749960997 usec\nrounds: 4323"
          },
          {
            "name": "tests/test_benchmark.py::test_map_pk_oral_benchmark",
            "value": 54.46304866940978,
            "unit": "iter/sec",
            "range": "stddev: 0.0002653340477827989",
            "extra": "mean: 18.36107277192636 msec\nrounds: 57"
          },
          {
            "name": "tests/test_benchmark.py::test_map_pk_iv_benchmark",
            "value": 50.25051269858794,
            "unit": "iter/sec",
            "range": "stddev: 0.0005609347194647054",
            "extra": "mean: 19.90029447058956 msec\nrounds: 51"
          },
          {
            "name": "tests/test_benchmark.py::test_tost_benchmark",
            "value": 9123.288481275938,
            "unit": "iter/sec",
            "range": "stddev: 0.00001926335567357625",
            "extra": "mean: 109.60959987753724 usec\nrounds: 3264"
          }
        ]
      }
    ]
  }
}