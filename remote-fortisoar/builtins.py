"""
Copyright start
MIT License
Copyright (c) 2024 Fortinet Inc
Copyright end
"""

from .operations import make_api_call, upload_file, invoke_agent

supported_operations = {'make_api_call': make_api_call, 'upload_file': upload_file, 'invoke_agent': invoke_agent}