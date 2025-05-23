import pandas as pd
import numpy as np
import statsmodels.api as sm
from tqdm import tqdm
import pickle
import os
import warnings
warnings.filterwarnings('ignore')

class NeutralizationProcessor:
    def __init__(self, barra_path, factor_path, industry, output_folder, mode):
        self.barra_path = barra_path
        self.factor_path = factor_path
        self.industry = industry
        self.output_folder = output_folder
        self.mode = mode

    def neutralize(self, factor_df, tar_col, barra_col, mode):
        result = pd.DataFrame()
        for col in tar_col:
            edge_up = factor_df[col].mean() + 3 * factor_df[col].std()
            edge_low = factor_df[col].mean() - 3 * factor_df[col].std()
            factor_df[col] = factor_df[col].clip(edge_low, edge_up)

            if mode == 1:
                factor_df[col] = (factor_df[col] - factor_df[col].min()) / (factor_df[col].max() - factor_df[col].min())
            elif mode == 2:
                factor_df[col] = (factor_df[col] - factor_df[tar_col].mean()) / factor_df[col].std()
            elif mode == 3:
                factor_df[col] = factor_df[col] / 10**np.ceil(np.log10(factor_df[col].abs().max()))

            results = sm.OLS(factor_df[col], factor_df[barra_col]).fit()
            result[col] = results.resid
        return result

    def process_data(self):
        barra_file = sorted(os.listdir(self.barra_path))
        factor_file = sorted(os.listdir(self.factor_path))

        for file in tqdm(barra_file):
            if file not in factor_file:
                continue
            date_tmp = file[:-4]
            factor = pd.read_csv(f'{self.factor_path}/{file}', index_col=0, header=0)
            barra_tmp = pd.read_csv(f'{self.barra_path}/{file}', index_col=0, header=0)
            industry_tmp = self.industry[date_tmp]

            target_list = barra_tmp.index.intersection(factor.index)
            target_list = industry_tmp.index.intersection(target_list)
            barra_tmp = barra_tmp.loc[target_list, :]
            industry_tmp = industry_tmp.loc[target_list, :]
            final = pd.concat([factor, barra_tmp, industry_tmp], axis=1)

            final.replace([np.inf, -np.inf], np.nan, inplace=True)
            final.fillna(0, inplace=True)

            final_col = barra_tmp.columns.tolist() + industry_tmp.columns.tolist()   #barra\hy
            col_name = factor.columns.tolist()
            data = self.neutralize(final, col_name, 'size', self.mode)
            data.to_csv(f'{self.output_folder}/{file}')

# # Configuration
# barra_path = './data/data_barra'
# factor_path = './feature/factor_final1'
# industry = pickle.load(open('./industry.pkl', 'rb'))
# output_folder = './neutralization/factor_final1_1'
# if not os.path.exists(output_folder):
#     os.makedirs(output_folder)
# mode = 3

# # Create and use the NeutralizationProcessor
# processor = NeutralizationProcessor(barra_path, factor_path, industry, output_folder, mode)
# processor.process_data()
