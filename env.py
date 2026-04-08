# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Environment entry point for OpenEnv validation.

This file provides the standard OpenEnv interface for the Mini Incident Response
Copilot environment. OpenEnv expects this file to exist at the project root.
"""

from .server.incident_response_environment import IncidentResponseEnvironment

# Export the environment class for OpenEnv
__all__ = ["IncidentResponseEnvironment"]
