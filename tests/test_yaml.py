import yaml


def test_load_yaml():
    with open("univ.yaml") as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)

    print(conf)
    print(conf["link"]["bb"])
    print(conf["user"]["cls"])

    if not conf["user"]["cls"]:
        print("hey")

    conf["user"]["cls"] = []
    conf["user"]["cls"].append({"code": 1, "name": 2})
    conf["user"]["cls"].append({"code": 3, "name": 4})

    with open("univ.yaml", "w") as f:
        yaml.dump(conf, f)

    print(conf["user"]["cls"])


if __name__ == "__main__":
    test_load_yaml()
