from dku_plugin_test_utils import dss_scenario


TEST_PROJECT_KEY = "PLUGINTESTGRAPHANALYTICS"


def test_run_all_recipes(user_dss_clients):
    dss_scenario.run(user_dss_clients, project_key=TEST_PROJECT_KEY, scenario_id="RUN_PLUGIN_GRAPH_ANALYTICS")
