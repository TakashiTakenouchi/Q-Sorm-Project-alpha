import { CloudUploadOutlined } from '@ant-design/icons';
import { Alert, Card, Layout, Tabs, Typography } from 'antd';
import type { TabsProps } from 'antd';
import { useEffect, useMemo, useState } from 'react';
import DataFilter from './components/common/DataFilter';
import UploadPanel from './components/common/UploadPanel';
import HistogramChart from './components/analysis/HistogramChart';
import LangchainNarrative from './components/analysis/LangchainNarrative';
import ParetoChart from './components/analysis/ParetoChart';
import TimeSeriesChart from './components/analysis/TimeSeriesChart';
import type { ChartFilters, UploadResponse } from './types';
import './App.css';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const App = () => {
  const [sessionId, setSessionId] = useState<string>('');
  const [uploadInfo, setUploadInfo] = useState<UploadResponse | null>(null);
  const [availableShops, setAvailableShops] = useState<string[]>([]);
  const [filters, setFilters] = useState<ChartFilters>({ shops: [] });
  const [activeKey, setActiveKey] = useState<'timeseries' | 'histogram' | 'pareto' | 'langchain'>('timeseries');

  const handleUploadSuccess = (response: UploadResponse) => {
    console.log('[App] ========== アップロード成功 ==========');
    console.log('[App] 完全なレスポンス:', JSON.stringify(response, null, 2));
    console.log('[App] セッションID:', response.session_id);
    console.log('[App] 店舗:', response.available_shops);
    console.log('[App] データ行数:', response.row_count);
    console.log('[App] ==========================================');

    setUploadInfo(response);
    setSessionId(response.session_id);
    setAvailableShops(response.available_shops ?? []);
    setFilters((prev) => ({
      ...prev,
      shops: response.available_shops ?? [],
    }));

    console.log('[App] State更新完了 - sessionId:', response.session_id);
  };

  useEffect(() => {
    console.log('[App] sessionId変更:', sessionId);
  }, [sessionId]);

  const handleFilterChange = (nextFilters: ChartFilters) => {
    setFilters(nextFilters);
  };

  const chartTabs: TabsProps['items'] = useMemo(
    () => {
      const selectedShops = filters.shops ?? [];
      return [
        {
          key: 'timeseries',
          label: '時系列',
          children: (
            <TimeSeriesChart
              sessionId={sessionId}
              shop={selectedShops.length > 0 ? selectedShops[0] : undefined}
              startDate={filters.startDate}
              endDate={filters.endDate}
            />
          ),
        },
        {
          key: 'histogram',
          label: 'ヒストグラム',
          children: (
            <HistogramChart
              sessionId={sessionId}
              shop={selectedShops.length > 0 ? selectedShops[0] : undefined}
              startDate={filters.startDate}
              endDate={filters.endDate}
            />
          ),
        },
        {
          key: 'langchain',
          label: 'AI解説',
          children: (
            <LangchainNarrative
              sessionId={sessionId}
              availableShops={availableShops}
              defaultStores={filters.shops ?? []}
            />
          ),
        },
        {
          key: 'pareto',
          label: 'パレート',
          children: (
            <ParetoChart
              sessionId={sessionId}
              shop={selectedShops.length > 0 ? selectedShops[0] : undefined}
              startDate={filters.startDate}
              endDate={filters.endDate}
            />
          ),
        },
      ];
    },
    [availableShops, filters, sessionId],
  );

  return (
    <Layout className="app-root">
      <Header className="app-header">
        <Typography.Title level={3} style={{ color: '#fff', margin: 0 }}>
          Q-Storm Platform v3.0
        </Typography.Title>
      </Header>
      <Layout>
        <Sider width={360} className="app-sider">
          <UploadPanel onUploadSuccess={handleUploadSuccess} />
          {uploadInfo && sessionId && (
            <Card size="small" style={{ marginBottom: 24 }} title="セッション情報">
              <p>
                <Text strong>セッションID</Text>
                <br />
                <Text copyable style={{ fontSize: 12, fontFamily: 'monospace' }}>
                  {sessionId}
                </Text>
              </p>
              <p>
                <Text strong>データ行数:</Text> {uploadInfo.row_count} 行
              </p>
              <p>
                <Text strong>利用可能な店舗:</Text> {availableShops.length ? availableShops.join(', ') : '未取得'}
              </p>
            </Card>
          )}
          <DataFilter availableShops={availableShops} filters={filters} onChange={handleFilterChange} />
        </Sider>
        <Content className="app-content">
          {!sessionId ? (
            <Alert
              message="データファイルをアップロードしてください"
              description="上部のアップロードパネルからExcelまたはCSVファイルをアップロードして分析を開始します。"
              type="info"
              icon={<CloudUploadOutlined />}
              showIcon
              style={{ maxWidth: 600, margin: '80px auto' }}
            />
          ) : (
            <Tabs
              activeKey={activeKey}
              onChange={(key) =>
                setActiveKey(key as 'timeseries' | 'histogram' | 'pareto' | 'langchain')
              }
              size="large"
              type="card"
              items={chartTabs}
            />
          )}
        </Content>
      </Layout>
    </Layout>
  );
};

export default App;
