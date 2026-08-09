from hashlib import sha256
import json

from macro_forecasting.manifest import sha256_file, write_run_manifest


def test_manifest_hashes_inputs_outputs_and_forecast_source(tmp_path, monkeypatch):
    config = tmp_path / "config.yml"
    data = tmp_path / "vintages.csv"
    output = tmp_path / "results"
    output.mkdir()
    config.write_text("benchmark:\n  protocol_version: '1.0.2'\n  seed: 1\n", encoding="utf-8")
    data.write_text("series_id,observation_date,vintage_date,value\nX,2020-01-01,2020-02-01,1\n", encoding="utf-8")
    (output / "leaderboard.csv").write_text("rank,model,score\n1,naive_last,1.0\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_SHA", "evaluation-sha")
    monkeypatch.setenv("FORECAST_SOURCE_SHA", "sealed-forecast-sha")

    manifest = write_run_manifest(config, data, output)

    assert manifest["config"]["sha256"] == sha256(config.read_bytes()).hexdigest()
    assert manifest["vintage_database"]["sha256"] == sha256(data.read_bytes()).hexdigest()
    assert manifest["result_sha256"]["leaderboard.csv"] == sha256_file(output / "leaderboard.csv")
    assert (output / "config_frozen.yml").read_text(encoding="utf-8") == config.read_text(encoding="utf-8")
    assert manifest["git_sha"] == "evaluation-sha"
    assert manifest["forecast_source_sha"] == "sealed-forecast-sha"
    assert manifest["benchmark_protocol_version"] == "1.0.2"
    loaded = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
    assert loaded["schema_version"] == 2
