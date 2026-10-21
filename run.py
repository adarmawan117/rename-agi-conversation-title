#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry point for Antigravity Conversation Renamer.
"""
import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main_gui import main

if __name__ == '__main__':
    main()
