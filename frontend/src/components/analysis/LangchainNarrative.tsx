import { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Card, Col, Empty, Row, Select, Skeleton, Space, Table, Typography, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  requestLangchainNarrative,
  type LangchainEvidenceDifference,
  type LangchainEvidenceStore,
} from '../../services/langchain';

const { Title, Paragraph, Text } = Typography;

type SelectOption = { label: string; value: string };

interface LangchainNarrativeProps {
  sessionId: string;
  availableShops: string[];
  defaultStores: string[];
}

interface RenderedLine {
  key: string;
  node: JSX.Element;
}

const LINE_BREAK = '\n';

const buildOptions = (shops: string[]): SelectOption[] =>
  shops.map((shop) => ({ label: shop, value: shop }));

const parseSummary = (summary: string): RenderedLine[] => {
  return summary.split(LINE_BREAK).map((line, index) => {
    const key = `${index}-${line}`;
    if (!line.trim()) {
      return { key, node: <br key={key} /> };
    }
    if (line.startsWith('## ')) {
      return { key, node: <Title level={4}>{line.replace('## ', '')}</Title> };
    }
    if (line.startsWith('- ')) {
      return {
        key,
        node: <Paragraph style={{ marginBottom: 4 }}>• {line.replace('- ', '')}</Paragraph>,
      };
    }
    return {
      key,
      node: <Paragraph>{line}</Paragraph>,
    };
  });
};

const LangchainNarrative = ({ sessionId, availableShops, defaultStores }: LangchainNarrativeProps) => {
  const [storeA, setStoreA] = useState<string | undefined>(defaultStores[0]);
  const [storeB, setStoreB] = useState<string | undefined>(defaultStores[1] ?? defaultStores[0]);
  const [loading, setLoading] = useState(false);
  const [summaryLines, setSummaryLines] = useState<RenderedLine[]>([]);
  const [differences, setDifferences] = useState<LangchainEvidenceDifference[]>([]);
  const [storeStats, setStoreStats] = useState<Record<string, LangchainEvidenceStore> | null>(null);

  useEffect(() => {
    if (!storeA || !availableShops.includes(storeA)) {
      setStoreA(availableShops[0]);
    }
    if (!storeB || !availableShops.includes(storeB)) {
      setStoreB(availableShops[1] ?? availableShops[0]);
    }
  }, [availableShops, storeA, storeB]);

  const canGenerate = useMemo(
    () => Boolean(sessionId && storeA && storeB && storeA !== storeB),
    [sessionId, storeA, storeB]
  );

  const handleGenerate = async () => {
    if (!canGenerate || !storeA || !storeB) {
      message.warning('異なる2店舗を選択してください');
      return;
    }
    setLoading(true);
    try {
      const data = await requestLangchainNarrative({
        session_id: sessionId,
        store_a: storeA,
        store_b: storeB,
      });
      setSummaryLines(parseSummary(data.summary));
      setDifferences(data.evidence?.differences ?? []);
      setStoreStats(data.evidence?.stores ?? null);
    } catch (error) {
      console.error('[LangchainNarrative] Failed:', error);
      message.error('LangChain解説の取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const differenceColumns: ColumnsType<LangchainEvidenceDifference & { key: number }> = [
    { title: 'カテゴリ', dataIndex: 'category', key: 'category' },
    {
      title: '店舗A',
      dataIndex: 'store_a',
      key: 'store_a',
      render: (value: number) => value?.toLocaleString(),
    },
    {
      title: '店舗B',
      dataIndex: 'store_b',
      key: 'store_b',
      render: (value: number) => value?.toLocaleString(),
    },
    {
      title: '差分',
      dataIndex: 'difference',
      key: 'difference',
      render: (value: number) => value?.toLocaleString(),
    },
  ];

  const options = buildOptions(availableShops);

  return (
    <Card
      title="Q-Storm Lang Agent"
      extra={
        <Space>
          <Select
            placeholder="店舗A"
            value={storeA}
            options={options}
            style={{ width: 160 }}
            onChange={setStoreA}
          />
          <Select
            placeholder="店舗B"
            value={storeB}
            options={options}
            style={{ width: 160 }}
            onChange={setStoreB}
          />
          <Button type="primary" onClick={handleGenerate} disabled={!canGenerate} loading={loading}>
            AI解説を生成
          </Button>
        </Space>
      }
    >
      {!sessionId ? (
        <Empty description="セッションが未選択です" />
      ) : loading ? (
        <Skeleton active paragraph={{ rows: 4 }} />
      ) : summaryLines.length === 0 ? (
        <Alert type="info" message="AI解説の生成を開始してください" showIcon />
      ) : (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            {summaryLines.map((line) => (
              <div key={line.key}>{line.node}</div>
            ))}
          </div>

          {storeStats && (
            <Row gutter={16}>
              {Object.entries(storeStats).map(([store, stats]) => (
                <Col span={12} key={store}>
                  <Card size="small" title={`${store} - 合計 ${stats.total.toLocaleString()} 円`}>
                    {stats.top_categories.length === 0 ? (
                      <Text type="secondary">カテゴリ情報なし</Text>
                    ) : (
                      <ul style={{ paddingLeft: 16, marginBottom: 0 }}>
                        {stats.top_categories.map((entry) => (
                          <li key={entry.category}>
                            {entry.category}: {entry.value.toLocaleString()} 円 ({entry.share_pct}%)
                          </li>
                        ))}
                      </ul>
                    )}
                  </Card>
                </Col>
              ))}
            </Row>
          )}

          {differences.length > 0 && (
            <Card size="small" title="差分上位カテゴリ">
              <Table
                size="small"
                dataSource={differences.map((item, index) => ({ ...item, key: index }))}
                columns={differenceColumns}
                pagination={false}
              />
            </Card>
          )}
        </Space>
      )}
    </Card>
  );
};

export default LangchainNarrative;
