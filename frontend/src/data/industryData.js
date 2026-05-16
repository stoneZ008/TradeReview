/**
 * 行业与龙头公司数据配置
 * 用于道页面展示行业信息和核心公司标的
 */
const industryData = [
  {
    id: 'optical-module',
    name: '光模块',
    icon: '📡',
    children: [
      {
        id: 'eml-chip',
        name: 'EML芯片',
        companies: [
          {
            code: '300394',
            name: '天孚通信',
            role: '光模块龙头',
            feature: '800G/1.6T高速光模块量产能力，绑定头部客户',
            desc: '光模块产品研发制造',
          },
          {
            code: '300502',
            name: '新易盛',
            role: '800G光模块',
            feature: '800G硅光模块领先，海外大客户突破',
            desc: '高速光模块供应商',
          },
          {
            code: '603083',
            name: '剑桥科技',
            role: '光模块',
            feature: '5G前传光模块，海外业务占比高',
            desc: '光通信产品',
          },
        ],
      },
      {
        id: 'cpo',
        name: 'CPO（共封装光学）',
        companies: [
          {
            code: '002281',
            name: '光迅科技',
            role: 'CPO龙头',
            feature: '国内光器件龙头，CPO方案储备充分',
            desc: '光通信器件',
          },
          {
            code: '300570',
            name: '太辰光',
            role: 'CPO',
            feature: '光无源器件，CPO封装布局',
            desc: '光无源器件',
          },
        ],
      },
      {
        id: 'silicon-photonics',
        name: '硅光',
        companies: [
          {
            code: '688800',
            name: '源杰科技',
            role: '硅光芯片',
            feature: '硅光芯片国产替代，25G/50G产品量产',
            desc: '光芯片',
          },
        ],
      },
    ],
  },
  {
    id: 'chip',
    name: '芯片',
    icon: '💾',
    children: [
      {
        id: 'gpu',
        name: 'GPU/AI芯片',
        companies: [
          {
            code: '688041',
            name: '海光信息',
            role: '国产GPU龙头',
            feature: '深海系列GPU，国产AI算力核心',
            desc: '国产GPU研发',
          },
          {
            code: '688256',
            name: '寒武纪',
            role: 'AI芯片',
            feature: '思元系列AI芯片，大模型训练推理',
            desc: 'AI芯片设计',
          },
        ],
      },
      {
        id: 'storage',
        name: '存储芯片',
        companies: [
          {
            code: '002049',
            name: '紫光国微',
            role: '存储芯片',
            feature: '国产存储芯片龙头，DRAM+NAND布局',
            desc: '存储芯片设计',
          },
        ],
      },
    ],
  },
  {
    id: 'server',
    name: '服务器/算力',
    icon: '🖥️',
    children: [
      {
        id: 'ai-server',
        name: 'AI服务器',
        companies: [
          {
            code: '000977',
            name: '浪潮信息',
            role: 'AI服务器龙头',
            feature: '国内AI服务器市占率第一，深度绑定英伟达',
            desc: '服务器研发制造',
          },
          {
            code: '603019',
            name: '中科曙光',
            role: '算力',
            feature: '国产算力基础设施，海光生态',
            desc: '高性能计算',
          },
        ],
      },
    ],
  },
  {
    id: 'new-energy',
    name: '新能源',
    icon: '⚡',
    children: [
      {
        id: 'pv',
        name: '光伏',
        companies: [
          {
            code: '300750',
            name: '宁德时代',
            role: '动力电池龙头',
            feature: '全球动力电池市占率第一',
            desc: '动力电池研发制造',
          },
        ],
      },
    ],
  },
];

export default industryData;
