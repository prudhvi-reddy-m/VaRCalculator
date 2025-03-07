import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from scipy.stats import norm
import altair as alt
#import plotly.express as px

# Page Configuration
st.set_page_config(
    page_title="VaR Calculator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

# VaR Class Definition
class VaR:
    def __init__(self, ticker, start_date, end_date, rolling_window, confidence_level, portfolio_val):
        self.ticker = ticker
        self.start = start_date
        self.end = end_date
        self.rolling = rolling_window
        self.conf_level = confidence_level
        self.portf_val = portfolio_val
        self.historical_var = None
        self.parametric_var = None
        
        self.data()
        
    def data(self):
        df = yf.download(self.ticker, self.start, self.end, auto_adjust=False)
        self.adj_close_df = df["Adj Close"]
        self.log_returns_df = np.log(self.adj_close_df / self.adj_close_df.shift(1))
        self.log_returns_df = self.log_returns_df.dropna()
        self.equal_weights = np.array([1 / len(self.ticker)] * len(self.ticker))
        historical_returns = (self.log_returns_df * self.equal_weights).sum(axis=1)
        self.rolling_returns = historical_returns.rolling(window=self.rolling).sum()
        self.rolling_returns = self.rolling_returns.dropna()
        self.historical_method()
        self.parametric_method()

    def historical_method(self):
        historical_VaR = -np.percentile(self.rolling_returns, 100 - (self.conf_level * 100)) * self.portf_val
        self.historical_var = historical_VaR

    def parametric_method(self):
        self.cov_matrix = self.log_returns_df.cov() * 252
        self.portfolio_std = np.sqrt(np.dot(self.equal_weights.T, np.dot(self.cov_matrix, self.equal_weights)))
        parametric_VaR = self.portfolio_std * norm.ppf(self.conf_level) * np.sqrt(self.rolling / 252) * self.portf_val
        self.parametric_var = parametric_VaR

    def plot_var_results(self, title, var_value, returns_dollar, conf_level):

        # Adjust the figure size to make the chart fit half page
        plt.figure(figsize=(12, 6))
        plt.hist(returns_dollar, bins=50, density=True)
        plt.xlabel(f'\n {title} VaR = ${var_value:.2f}')
        plt.ylabel('Frequency')
        plt.title(f"Distribution of Portfolio's {self.rolling}-Day Returns ({title} VaR)")
        plt.axvline(-var_value, color='r', linestyle='dashed', linewidth=2, label=f'VaR at {conf_level:.0%} confidence level')
        plt.legend()
        plt.tight_layout()
        return plt
    
if 'recent_outputs' not in st.session_state:
    st.session_state['recent_outputs'] = []


# Sidebar for User Inputs
with st.sidebar:
    st.title('📈 VaR Calculator')
    st.write("`Created by:`")
    linkedin_url = "https://www.linkedin.com/in/mprudhvi/"
    st.markdown(f'<a href="{linkedin_url}" target="_blank" style="text-decoration: none; color: inherit;"><img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" width="25" height="25" style="vertical-align: middle; margin-right: 10px;">`Prudhvi Reddy, Muppala`</a>', unsafe_allow_html=True)

    tickers = st.text_input('Enter tickers separated by space', 'AAPL MSFT GOOG').split()
    start_date = st.date_input('Start date', value=pd.to_datetime('2020-01-01'))
    end_date = st.date_input('End date', value=pd.to_datetime('today'))
    rolling_window = st.slider('Rolling window', min_value=1, max_value=252, value=20)
    confidence_level = st.slider('Confidence level', min_value=0.90, max_value=0.99, value=0.95, step=0.01)
    portfolio_val = st.number_input('Portfolio value', value=100000)
    calculate_btn = st.button('Calculate VaR')



####

def calculate_and_display_var(tickers, start_date, end_date, rolling_window, confidence_level, portfolio_val):
    var_instance = VaR(tickers, start_date, end_date, rolling_window, confidence_level, portfolio_val)
    
    # Layout for charts
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.info("Historical VaR Chart")
        historical_chart = var_instance.plot_var_results("Historical", var_instance.historical_var, var_instance.rolling_returns * var_instance.portf_val, confidence_level)
        st.pyplot(historical_chart)

    with chart_col2:
        st.info("Parametric VaR Chart")
        parametric_chart = var_instance.plot_var_results("Parametric", var_instance.parametric_var, var_instance.rolling_returns * var_instance.portf_val, confidence_level)
        st.pyplot(parametric_chart)

    # Layout for input summary and recent VaR values
    col1, col3 = st.columns([1, 1])
    
    with col1:
        st.info("Input Summary")
        st.write(f"Tickers: {tickers}")
        st.write(f"Start Date: {start_date}")
        st.write(f"End Date: {end_date}")
        st.write(f"Rolling Window: {rolling_window} days")
        st.write(f"Confidence Level: {confidence_level:.2%}")
        st.write(f"Portfolio Value: ${portfolio_val:,.2f}")


    with col3:
        st.info("VaR Calculation Output")
        data = {
            "Method": ["Historical", "Parametric"],
            "VaR Value": [f"${var_instance.historical_var:,.2f}", f"${var_instance.parametric_var:,.2f}"]
        }
        df = pd.DataFrame(data)
        st.table(df)

    st.session_state['recent_outputs'].append({
        "Historical": f"${var_instance.historical_var:,.2f}",
        "Parametric": f"${var_instance.parametric_var:,.2f}"
    })

    # Display Recent VaR Output table
    with col3:
        st.info("Previous VaR Calculation Outputs")
        # Convert the list of recent outputs to a DataFrame for display
        recent_df = pd.DataFrame(st.session_state['recent_outputs'])
        st.table(recent_df)

#####
if 'first_run' not in st.session_state or st.session_state['first_run']:
    st.session_state['first_run'] = False
    # Default values for first run
    default_tickers = 'AAPL MSFT GOOG'.split()
    default_start_date = pd.to_datetime('2020-01-01')
    default_end_date = pd.to_datetime('today')
    default_rolling_window = 20
    default_confidence_level = 0.95
    default_portfolio_val = 100000

    # Perform the default calculation
    calculate_and_display_var(default_tickers, default_start_date, default_end_date, default_rolling_window, default_confidence_level, default_portfolio_val)



# Display Results on Button Click
if calculate_btn:
    calculate_and_display_var(tickers, start_date, end_date, rolling_window, confidence_level, portfolio_val)
