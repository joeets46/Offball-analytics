# Databricks notebook source
# MAGIC %run ./00_gold_runtime_config
# MAGIC %run ./03_publication_helpers


if __name__ == "__main__":
    finalize_publication(GOLD_CONFIG)
