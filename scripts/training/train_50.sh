#!/bin/bash

#SBATCH --partition=gpu2 # GPU2 partition
#SBATCH --ntasks=1       # 1 CPU core to drive GPU
#SBATCH --gres=gpu:1     # Request 1 GPU
#SBATCH --mail-type=ALL
#SBATCH --mail-user=eddiecwilliams@gmail.com
#SBATCH --output=top-50-%j.out
#SBATCH --error=top-50-%j.err

module load cuda/9.1

#SIGNS='["na","HAL","iš","MEŠ"]'
#SIGNS='["na","HAL"]'
#SIGNS='["na","HAL","iš","MEŠ","ma","1","du","da","AN","AŠ"]'
SIGNS='["na","HAL","iš","MEŠ","ma","1","du","da","AN","AŠ","ka₄","kur","2","ba","ra","šá","be","20","3","SAL","ul","ITI","ia","KI","MIN","hu","man","QA","me","mi","ti","um","m°n","ha","10","taš","ak","ri","BAR","4","gal","pu","ku","ir","mar","ip","´","ki","an","5"]'


luigi --module deepscribe.luigi.training TrainKerasModelFromDefinitionTask --local-scheduler \
      --imgfolder data/ochre/a_pfa \
      --hdffolder data/processed/pfa_new \
      --modelsfolder models \
      --target-size 50 \
      --keep-categories $SIGNS  \
      --fractions '[0.7, 0.1, 0.2]' \
      --model-definition data/model_defs/alexnet-small_256epoch.json \
      --num-augment 0
