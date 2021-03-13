#!/usr/bin/env python3
# encoding: utf-8

from cortexutils.analyzer import Analyzer

import requests


class StamusNetworksAnalyzer(Analyzer):
    def __init__(self):
        Analyzer.__init__(self)
        self.api_key = self.get_param('config.key', None, 'Scirius Security Platform api key is missing')
        self.base_url = self.get_param('config.url', None, 'Scirius Security Platform url is missing')
        self.base_url = self.base_url.rstrip('/ ')
        self.ssl_verify = self.get_param('config.ssl_verify', None, 'Scirius Security Platform TLS verification info is missing')
        self.proxies = {
                "https" : self.get_param("config.proxy_https", None),
                "http" : self.get_param("config.proxy_http", None)
                }
        self.session = requests.Session()
        self.session.headers.update({ 'Content-Type': 'application/json', 'Authorization': 'Token ' + self.api_key })

    def artifacts(self, raw):
        artifacts = []
        hostnames = raw['host_id'].get('hostname', [])
        for host in hostnames:
            tags=["first-seen:" + host['first_seen'], "last-seen:" + host['last_seen']]
            artifacts.append(
                    self.build_artifact('fqdn',
                        host['host'],
                        tags=tags))
        return artifacts

    def summary(self, raw):
        taxonomies = []
        namespace = "SSP"
        value = raw["host_id"]["first_seen"]
        taxonomies.append(self.build_taxonomy("info", namespace, 'first-seen', value))
        value = raw["host_id"]["last_seen"]
        taxonomies.append(self.build_taxonomy("info", namespace, 'last-seen', value))

        value = raw["host_id"].get("services_count")
        if value:
            taxonomies.append(self.build_taxonomy("info", namespace, 'services', value))
        value = raw["host_id"].get("tls.ja3_count")
        if value:
            taxonomies.append(self.build_taxonomy("info", namespace, 'tls-agents', value))
        value = raw["host_id"].get("http.user_agent_count")
        if value:
            taxonomies.append(self.build_taxonomy("info", namespace, 'http-agents', value))

        return {"taxonomies": taxonomies}

    def run(self):
        Analyzer.run(self)
        info = {}
        try:
            if self.data_type == 'ip':
                url = self.base_url + "/rest/appliances/host_id/" + self.get_data()
                resp = self.session.get(url, verify=self.ssl_verify, proxies=self.proxies)
                info = resp.json()
            # TODO add support for user-agent and fqdn
            else:
                self.error('Invalid data type !')

            self.report(info)

        except Exception as e:
            self.unexpectedError(e)


if __name__ == '__main__':
    StamusNetworksAnalyzer().run()
