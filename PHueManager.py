from requests import request
# Disable insecure warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Device(object):
    def __init__(self, device_data=None, device_type=None):
        self.device_data = device_data
        self.device_type = device_type


class Hue(object):
    def __init__(self, proto='https', api_root='/clip/v2/', address=None, app_key=None):
        """
        Philips Hue class
        :param proto:
        :param api_root:
        :param address:
        :param app_key:
        """
        self.address = address
        self.app_key = app_key
        self.proto = proto
        self.api_root = api_root
        self.base = self.proto + '://' + self.address + self.api_root
        self.headers = {'hue-application-key': self.app_key}
        self.devices = []
        self.bridge = ''
        self.services = []

        # Generate list of devices
        tmp = self.device(method='get')
        if 'data' in tmp.json():
            self.parse_devices(tmp.json())

        # Entertainment stuff
        self.raw_ents = self.get_ent_config()
        self.ent_configs = []
        if isinstance(self.raw_ents, dict):
            self.parse_ent_conf()

    def sw_version(self):
        """
        Get Philips Hue Software Version details.
        :return:
        """
        sw_version = "/api/config"
        url = self.proto + '://' + self.address + sw_version
        response = request(method='get', url=url, verify=False)
        return response

    def device(self, method=None):
        url = self.base + 'resource/device'
        response = request(method=method, url=url, headers=self.headers, verify=False)
        if self.valid_response(response):
            return response
        else:
            return None

    def parse_devices(self, raw_device_data=None):
        for dt in ['bridge_v2', 'sultan_bulb']:
            for item in raw_device_data['data']:
                if item['metadata']['archetype'] == dt:
                    self.devices.append(Device(device_data=item, device_type=dt))
                    tmp = {
                        'name': item['metadata']['name'],
                        'services': item['services']
                    }
                    self.services.append(tmp)
        return

    def fetch_names_of_type(self, type=None):
        """
        Fetch device names of a given device type
        example fetch_names_of_type(type='sultan_bulb')
        :param type:
        :return:
        """
        device_list = []
        for device in self.devices:
            if device.device_type == type:
                device_list.append(device.device_data['metadata']['name'])
        return device_list

    def get_device_details_by_name(self, name=None):
        """
        Get the device details by the device name.
        example;
        hue.get_device_details_by_name(name='Lounge Rear ceiling')
        :param name: device name
        :return: device data (JSON) dict
        """
        for device in self.devices:
            if device.device_data['metadata']['name'] == name:
                return device.device_data
        return

    def get_device_rid(self, name=None, rtype=None):
        """
        Get device rid information based on name and type
        eg,
        get_device_rid(name='Lounge Rear ceiling', rtype='entertainment')
        :param name: device name
        :param rtype: rtype
        :return: dictionary of rid information
        """
        rid_dict = {}
        for device in self.devices:
            if device.device_data['metadata']['name'] == name:
                services = device.device_data['services']
                for service in services:
                    if service['rtype'] == rtype:
                        rid_dict.update(
                            {"rid": service['rid'],
                             "rtype": service['rtype']}
                        )
        return rid_dict

    def light_body(self, name=None, rid=None, method=None, resource=None, body=None):
        """
        Method used to freely declare action body with no sanity check within method etc.
        Handy if setting multiple function values.
        :param name: Light name
        :param method: put is required to change setting
        :param resource: device resource 'resource/light'
        :param rid: optional value for rid, rids take precedence over names
        :param body: JSON Body compatible with light device api
        :return:
        """
        RTYPE = 'light'
        if rid:
            url = self.base + resource + '/' + rid
        else:
            url = self.base + resource + '/' + ((self.get_device_rid(name=name, rtype=RTYPE))['rid'])
        response = request(method=method, url=url, headers=self.headers, verify=False, json=body)
        return response

    def light_state(self, name=None, method=None, resource=None, on=None):
        """
        Used to control set a light on or off.  Light is selected by Name.
        Example;
        hue.light_control(name='Lounge Rear ceiling', method='put', resource='resource/light', on=True)
        :param name: Light name
        :param method: put is required to change setting
        :param resource: device resource 'resource/light'
        :param on: Boolean, True for on, False for off
        :return:
        """
        RTYPE = 'light'
        body = {
            "on": {
                "on": on
            }
        }
        url = self.base + resource + '/' + ((self.get_device_rid(name=name, rtype=RTYPE))['rid'])
        response = request(method=method, url=url, headers=self.headers, verify=False, json=body)
        return response

    def light_dimming(self, name=None, method=None, resource=None, dim_val=None):
        """
        Controls the brightness of the bulb, Will sanity check dim_val, and limit extremes.
        Example;
        light_dimming(name='TV Room Lamp stand', method='put', resource='resource/light', dim_val=100)
        :param name: Light name
        :param method: put is required to change setting
        :param resource: device resource 'resource/light'
        :param dim_val: Float, Dimming value 0 - 100.
        :return:
        """
        RTYPE = 'light'
        if dim_val > 100: dim_val = 100
        if dim_val < 0: dim_val = 0

        body = {
            "dimming": {
                "brightness": dim_val
            }
        }
        url = self.base + resource + '/' + ((self.get_device_rid(name=name, rtype=RTYPE))['rid'])
        response = request(method=method, url=url, headers=self.headers, verify=False, json=body)
        return response

    def light_temp(self, name=None, method=None, resource=None, temp_k=None):
        """
        Controls the color temperatur of the bult.
        Hue supports color temperatures from 2000K (warm) to 6500K (cold) with high quality white light.
        To set the light to a white value you need to interact with the “color_temperature” object, which takes values
        in a scale called “reciprocal megakelvin” or “mirek”. Using this scale, the warmest color 2000K is 500 mirek
        and the coldest color 6500K is 153 mirek.
        Example;
        light_temp(name='TV Room Lamp stand', method='put', resource='resource/light', temp_k=val)
        :param name: Light name
        :param method: put is required to change setting
        :param resource: device resource 'resource/light'
        :param temp_k: Color temperature based on the “reciprocal megakelvin” or “mirek” scale, 500 warmest, 153 cold
        :return:
        """
        RTYPE = 'light'
        if temp_k > 500:
            temp_k = 500

        if temp_k < 153:
            temp_k = 153

        body = {
            "color_temperature": {
                "mirek": temp_k
            }
        }
        url = self.base + resource + '/' + ((self.get_device_rid(name=name, rtype=RTYPE))['rid'])
        response = request(method=method, url=url, headers=self.headers, verify=False, json=body)
        return response

    def light_colour(self, name=None, method=None, resource=None, color=None):
        """
        Controls the colour of a bulb.
        Example;
        light_colour(name='TV Room Lamp stand', method='put', resource='resource/light',color={"x": 0.11, "y": 0.3})
        print(control)
        :param name: Light name
        :param method: put is required to change setting
        :param resource: device resource 'resource/light'
        :param color: Dict Colour specification {"x": 0.11, "y": 0.3} based on CIE chromaticity diagram
        :return:
        """
        RTYPE = 'light'
        if color:
            x_val = color["x"]
            if x_val > 1: x_val = 1
            y_val = color["y"]
            if y_val > 1: y_val = 1
        else:
            x_val = 0.1
            y_val = 0.1
        body = {
            "color": {
                "xy": {
                    "x": x_val,
                    "y": y_val
                }
            }
        }
        url = self.base + resource + '/' + ((self.get_device_rid(name=name, rtype=RTYPE))['rid'])
        response = request(method=method, url=url, headers=self.headers, verify=False, json=body)
        return response

    def get_ent_config(self, method='get', resource="resource/entertainment_configuration"):
        url = self.base + resource
        response = request(method=method, url=url, headers=self.headers, verify=False)
        if self.valid_response(response):
            return response.json()
        return response

    def parse_ent_conf(self):
        for ent in self.raw_ents['data']:
            self.ent_configs.append({
                'id': ent['id'],
                'name': ent['name'],
                'status': ent['status'],
                'type': ent['type'],
                'light_service': ent['light_services']
            })
        return

    def get_ent_id(self, name=None):
        id_dict = {}
        for ent_item in self.ent_configs:
            if ent_item['name'] == name:
                id_dict.update({"id": ent_item['id']})
        return id_dict

    def ent_status_name(self, method=None, name=None, resource="resource/entertainment_configuration", id_val=None,
                        action=None):
        """
                Address	https://<bridge IP address>/clip/v2/entertainment_configuration/<id>
        :param method:
        :param name:
        :param status:
        :param resource:
        :param id:
        :param action:
        :return:
        """
        if not id_val:
            id_val = (self.get_ent_id(name=name))['id']

        url = self.base + resource + "/" + id_val

        if action:
            action = "start"
        else:
            action = "stop"

        body = {"action": action}
        response = request(method=method, url=url, headers=self.headers, verify=False, json=body)
        return response

    @staticmethod
    def valid_response(response):
        if response.status_code == 200:
            return True
        if response.status_code == 404:
            return True
        else:
            return False
