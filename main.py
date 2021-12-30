from PHueManager import Hue
import yaml
import time
import random

CONFIG_FILE = 'config.yml'
PHILIPS_HUE = 'PhilipsHue'
APP_KEY_NAME = 'HUE-APPLICATION-KEY'
IPADDR = 'IPADDR'
S_BULB_TYPE = 'sultan_bulb'


def get_config(config_file):
    """
    Read in the configuration
    :param config_file:
    :return:
    """
    try:
        config = ''
        with open(config_file, "r") as yaml_file:
            config = yaml.load(yaml_file, Loader=yaml.FullLoader)
            print("Config read successful, {}".format(config))
    except Exception as e:
        print("Ooops! Error occurred reading configs, {}".format(e))
    return config


def random_color():
    x = random.uniform(0, 1)
    y = random.uniform(0, 1)
    return {"xy": {"x": x, "y": y}}


def random_brightness():
    dim_val = random.uniform(0, 100)
    return {"brightness": dim_val}


def build_crazy_body():
    body = {
        "dimming": random_brightness(),
        "color": random_color()
        }
    return body


def convert_names_to_rids(hue=None, names=None):
    """
    Converts a list of names to a list of rid values
    :param hue:
    :parm names: optional names list
    :return:
    """
    rids = []
    if not names:
        names = hue.fetch_names_of_type(type=S_BULB_TYPE)
    for name in names:
        rid = hue.get_device_rid(name=name, rtype='light')
        rids.append(rid['rid'])
    return rids


def random_sync(hue=None, duration=None, sleep_val=None):
    """
    Random lighting using API, all available lights sync'd
    :param hue: instance of Hue class
    :param duration: loop duration
    :return:
    """
    y = 0
    names = hue.fetch_names_of_type(type=S_BULB_TYPE)
    while y < duration:
        body = build_crazy_body()
        for light in names:
            control = hue.light_body(name=light, method='put', resource='resource/light', body=body)
        if sleep_val:
            time.sleep(sleep_val)
        y += 1
    return


def random_lights(hue=None, duration=None, sleep_val=None):
    """
    Random lights, each light is not sync'd
    :param hue: instance of Hue class
    :param duration: loop / number of changes
    :param sleep_val: sleep between changes
    :return:
    """
    y = 0
    names = hue.fetch_names_of_type(type=S_BULB_TYPE)
    while y < duration:
        for light in names:
            control = hue.light_body(name=light, method='put', resource='resource/light', body=build_crazy_body())
        if sleep_val:
            time.sleep(sleep_val)
        y += 1
    return


def random_lights_by_rid(hue=None, duration=None, sleep_val=None):
    """
    Random lights, each light is not sync'd
    :param hue: instance of Hue class
    :param duration: loop / number of changes
    :param sleep_val: sleep between changes
    :return:
    """
    y = 0
    rids = []
    rids = convert_names_to_rids(hue=hue)
    while y < duration:
        for rid in rids:
            control = hue.light_body(rid=rid, method='put', resource='resource/light', body=build_crazy_body())
        if sleep_val:
            time.sleep(sleep_val)
        y += 1
    return


def bounce_brilliance(hue=None, duration=None, color=None, names=None, increment=None):
    rids = convert_names_to_rids(hue=hue)
    dim_val = 1
    y = 0
    direction_up = True
    if not increment:
        increment = 1

    while y < duration:
        if color:
            body = {
                "color": {"xy": {"x": color["x"], "y": color["y"]}},
                "dimming": {"brightness": dim_val}
            }
        else:
            body = {"dimming": {"brightness": dim_val}}

        for rid in rids:
            control = hue.light_body(rid=rid, method='put', resource='resource/light', body=body)
        print("DIM VAL {} DIRECT UP {}".format(dim_val, direction_up))
        if dim_val < 100 and direction_up:
            dim_val += increment

        if dim_val > 99:
            direction_up = False
            dim_val -= increment

        if dim_val > 0 and not direction_up:
            dim_val -= increment

        if dim_val < 99 and not direction_up:
            dim_val -= increment

        if dim_val < 0:
            direction_up = True
            dim_val = 0

        y += 1
    return

def main():
    configs = False
    hue_application_key = ''
    ipaddr = ''

    config = get_config(CONFIG_FILE)
    if config:
        hue_application_key = config[0][PHILIPS_HUE][APP_KEY_NAME]
        ipaddr = config[0][PHILIPS_HUE][IPADDR]
        configs = True

    if configs:
        hue = Hue(address=ipaddr, app_key=hue_application_key)

        names = hue.fetch_names_of_type(type=S_BULB_TYPE)
        print(names)
        for dv in hue.devices:
            print(dv.__dict__)
        print(hue.ent_configs)
        test = hue.ent_status_name(method='put', name='Test', resource="resource/entertainment_configuration",
                                   action=True)
        print(test.json())

        test2 = True
        if test2:
            random_lights_by_rid(hue=hue, duration=100)
            #bounce_brilliance(hue=hue, duration=100, increment=10, color={'x': 0.4, 'y':0.1 })

        test = False
        if test:
            x = 0
            while x < 50:
                list = ["Lounge Lamp stand", "Lounge Rear ceiling", "Lounge Front ceiling"]
                for item in list:
                    control = hue.light_state(name=item, method='put', resource='resource/light', on=False)
                    print(control.reason)
                    time.sleep(1)
                    control = hue.light_state(name=item, method='put', resource='resource/light', on=True)
                    x += 1


if __name__ == '__main__':
    main()