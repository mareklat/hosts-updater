#!/usr/bin/env python3
import argparse
import configparser
import logging
import requests
import os
import sys
from pathlib import Path

try:
    import colorlog
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s %(levelname)-8s%(reset)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    ))
    logging.basicConfig(handlers=[handler], level=logging.INFO)
except ImportError:
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO
    )

logger = logging.getLogger(__name__)

class HostsUpdater:
    def __init__(self):
        logger.info("Initializing HostsUpdater")
        self.config = self._load_config()
        logger.debug("Configuration loaded: %s", {k: '****' if k in ['password'] else v for k, v in self.config.items()})
        
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        logger.debug("Created requests session with headers: %s", self.session.headers)
        
        self._authenticate()

    def _authenticate(self):
        login_url = f"{self.config['api_url']}/api/tokens"
        try:
            response = self.session.post(login_url, json={
                'identity': self.config['username'],
                'secret': self.config['password']
            })
            response.raise_for_status()
            token = response.json()['token']
            self.session.headers.update({
                'Authorization': f'Bearer {token}'
            })
            logger.info("Successfully authenticated with API")
            logger.debug("Updated session headers with auth token")
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            sys.exit(1)

    def _load_config(self):
        # Find config.ini next to executable
        exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        config_path = os.path.join(exe_dir, 'config.ini')
        
        if not os.path.exists(config_path):
            logger.error(f"Config file not found at {config_path}")
            sys.exit(1)

        config = configparser.ConfigParser()
        config.read(config_path)
        
        # Prompt for credentials during runtime
        username = input("Enter NPM username: ")
        from getpass import getpass
        password = getpass("Enter NPM password: ")
        
        return {
            'username': username,
            'password': password,
            'api_url': config['nginx-proxy-manager']['api_url'],
            'ip_address': config['nginx-proxy-manager']['ip_address'],
            'section_header': config['hosts']['section_header'],
            'section_footer': config['hosts']['section_footer'],
            'hosts_file': config['hosts'].get('file_path', '/etc/hosts')
        }

    def get_domains(self):
        try:
            response = self.session.get(f"{self.config['api_url']}/api/nginx/proxy-hosts")
            response.raise_for_status()
            domains = [proxy['domain_names'][0] for proxy in response.json()]
            logger.info("Fetched %d domains from API", len(domains))
            logger.debug("Domain list: %s", domains)
            return domains
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching domains: {e}")
            sys.exit(1)

    def update_hosts_file(self, domains):
        hosts_path = self.config['hosts_file']
        try:
            with open(hosts_path, 'r+') as f:
                content = f.read()
                
                # Remove existing section if present
                header = self.config['section_header']
                footer = self.config['section_footer']
                start = content.find(header)
                end = content.find(footer)
                
                if start != -1 and end != -1:
                    logger.info("Found existing section in hosts file, removing it")
                    content = content[:start] + content[end + len(footer):]
                else:
                    logger.info("No existing section found in hosts file")
                
                # Add new section
                new_section = f"\n{header}\n"
                new_section += "\n".join(f"{self.config['ip_address']} {domain}" for domain in domains)
                new_section += f"\n{footer}\n"
                logger.debug("Prepared new section for hosts file")
                
                f.seek(0)
                f.write(content + new_section)
                f.truncate()
                
        except PermissionError:
            logger.error("Need root privileges to modify /etc/hosts")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error updating hosts file: {e}")
            sys.exit(1)

    def run(self):
        domains = self.get_domains()
        self.update_hosts_file(domains)
        logger.info(f"Successfully updated /etc/hosts with {len(domains)} domains")
        logger.debug("Updated domains: %s", domains)

if __name__ == '__main__':
    updater = HostsUpdater()
    updater.run()
