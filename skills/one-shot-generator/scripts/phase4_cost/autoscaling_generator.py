#!/usr/bin/env python3
"""Autoscaling Generator"""
from typing import Dict

class AutoscalingGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['autoscaling_config.yaml'] = self._autoscaling()
        return files

    def _autoscaling(self) -> str:
        return '''apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  minReplicas: 2
  maxReplicas: 10
'''
