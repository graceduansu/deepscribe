#!/bin/bash


luigi --module deepscribe.pipeline.selection SelectDatasetTask --local-scheduler \
      --imgfolder ../deepscribe-data/ochre/a_pfa \
      --hdffolder ../deepscribe-data/processed/pfa_new \
      --target-size 50 \
      --keep-categories data/charsets/top50.txt \
      --fractions '[0.7, 0.1, 0.2]' \
      --sigma 0.5