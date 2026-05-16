import { useState, useCallback } from 'react';
import { fetchStockData, runBacktest } from '../api';

export const useStockData = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stockData, setStockData] = useState(null);
  const [backtestResult, setBacktestResult] = useState(null);

  const getStockData = useCallback(async (symbol, startDate, endDate) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchStockData(symbol, startDate, endDate);
      setStockData(data);
      return data;
    } catch (e) {
      setError(e.message);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const runBacktestAnalysis = useCallback(async (symbol, startDate, endDate, config = {}) => {
    setLoading(true);
    setError(null);
    try {
      const result = await runBacktest(symbol, startDate, endDate, config);
      setBacktestResult(result);
      return result;
    } catch (e) {
      setError(e.message);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearData = useCallback(() => {
    setStockData(null);
    setBacktestResult(null);
  }, []);

  return {
    loading,
    error,
    stockData,
    backtestResult,
    getStockData,
    runBacktestAnalysis,
    clearData
  };
};
