import React, { useState, useEffect } from 'react';
import CompanyCard from './CompanyCard';
import { useAuth } from '../context/AuthContext';
import { API_BASE, fetchWithAuth } from '../api';

function DaoPage({ onStockSelect }) {
  const { hasRole } = useAuth();
  const canEdit = hasRole('admin') || hasRole('super_admin');
  const [industryData, setIndustryData] = useState([]);
  const [selectedIndustry, setSelectedIndustry] = useState(null);
  const [selectedSubIndustry, setSelectedSubIndustry] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editingCompany, setEditingCompany] = useState(null);
  const [newCompany, setNewCompany] = useState({
    code: '',
    name: '',
    role: '',
    feature: '',
    desc: '',
  });
  const [addCompanySubId, setAddCompanySubId] = useState(null);

  // 子行业表单状态
  const [showAddSubForm, setShowAddSubForm] = useState(false);
  const [showEditSubForm, setShowEditSubForm] = useState(false);
  const [editingSubIndustry, setEditingSubIndustry] = useState(null);
  const [newSubIndustry, setNewSubIndustry] = useState({
    name: '',
    companies: [],
  });

  // 一级行业表单状态
  const [showAddIndustryForm, setShowAddIndustryForm] = useState(false);
  const [showEditIndustryForm, setShowEditIndustryForm] = useState(false);
  const [editingIndustry, setEditingIndustry] = useState(null);
  const [newIndustry, setNewIndustry] = useState({
    id: '',
    name: '',
    icon: '🏢',
    children: [],
  });

  // 搜索状态
  const [searchKeyword, setSearchKeyword] = useState('');

  // 加载行业数据
  useEffect(() => {
    fetchIndustries();
  }, []);

  const fetchIndustries = async () => {
    try {
      const res = await fetchWithAuth(`${API_BASE}/industries`);
      const data = await res.json();
      if (data.data) {
        setIndustryData(data.data);
        let newIndustry = null;
        if (data.data.length > 0 && !selectedIndustry) {
          newIndustry = data.data[0];
          setSelectedIndustry(newIndustry);
        } else if (selectedIndustry) {
          const updated = data.data.find((i) => i.id === selectedIndustry.id);
          if (updated) {
            newIndustry = updated;
            setSelectedIndustry(updated);
          } else if (data.data.length > 0) {
            newIndustry = data.data[0];
            setSelectedIndustry(newIndustry);
          } else {
            setSelectedIndustry(null);
          }
        }
        // 同步子行业选中状态
        if (newIndustry && selectedSubIndustry) {
          const updatedSub = (newIndustry.children || []).find(
            (s) => s.id === selectedSubIndustry.id
          );
          if (updatedSub) {
            setSelectedSubIndustry(updatedSub);
          } else {
            setSelectedSubIndustry(
              (newIndustry.children || [])[0] || null
            );
          }
        } else if (newIndustry) {
          setSelectedSubIndustry((newIndustry.children || [])[0] || null);
        } else {
          setSelectedSubIndustry(null);
        }
      }
    } catch (e) {
      console.error('加载行业数据失败:', e);
    }
  };

  // 选择行业
  const selectIndustry = (industry) => {
    setSelectedIndustry(industry);
    setSelectedSubIndustry((industry.children || [])[0] || null);
    setShowAddForm(false);
    setShowEditForm(false);
    setShowAddSubForm(false);
    setShowEditSubForm(false);
    setAddCompanySubId(null);
  };

  // 选择子行业
  const selectSubIndustry = (sub) => {
    setSelectedSubIndustry(sub);
    setShowAddForm(false);
    setShowEditForm(false);
  };

  // 点击公司卡片
  const handleCompanySelect = (company) => {
    if (onStockSelect) {
      onStockSelect(company.code);
    }
  };

  // 开始添加公司
  const startAddCompany = () => {
    if (!selectedSubIndustry) return;
    setAddCompanySubId(selectedSubIndustry.id);
    setShowAddForm(true);
    setShowEditForm(false);
    setNewCompany({ code: '', name: '', role: '', feature: '', desc: '' });
  };

  // 添加公司
  const handleAddCompany = async () => {
    if (!newCompany.code || !newCompany.name) {
      alert('请填写公司代码和名称');
      return;
    }
    if (!addCompanySubId) {
      alert('请先选择一个子行业分类');
      return;
    }

    try {
      const res = await fetchWithAuth(`${API_BASE}/companies`, {
        method: 'POST',
        body: JSON.stringify({
          sub_industry_id: addCompanySubId,
          code: newCompany.code,
          name: newCompany.name,
          role: newCompany.role,
          feature: newCompany.feature,
          description: newCompany.desc,
        }),
      });
      const data = await res.json();

      if (data.success) {
        await fetchIndustries();
        setNewCompany({ code: '', name: '', role: '', feature: '', desc: '' });
        setShowAddForm(false);
        setAddCompanySubId(null);
      } else {
        alert(data.error || '添加失败');
      }
    } catch (e) {
      console.error('添加公司失败:', e);
      alert('添加失败');
    }
  };

  // 编辑公司
  const handleEditCompany = (company) => {
    setEditingCompany(company);
    setNewCompany({ ...company });
    setShowEditForm(true);
    setShowAddForm(false);
  };

  // 保存编辑
  const handleSaveEdit = async () => {
    if (!newCompany.code || !newCompany.name) {
      alert('请填写公司代码和名称');
      return;
    }
    if (!editingCompany) return;

    try {
      const res = await fetchWithAuth(`${API_BASE}/companies/${editingCompany.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          ...newCompany,
          description: newCompany.desc,
        }),
      });
      const data = await res.json();

      if (data.success) {
        await fetchIndustries();
        setEditingCompany(null);
        setNewCompany({ code: '', name: '', role: '', feature: '', desc: '' });
        setShowEditForm(false);
      } else {
        alert(data.error || '更新失败');
      }
    } catch (e) {
      console.error('更新公司失败:', e);
      alert('更新失败');
    }
  };

  // 取消编辑
  const handleCancelEdit = () => {
    setEditingCompany(null);
    setNewCompany({ code: '', name: '', role: '', feature: '', desc: '' });
    setShowEditForm(false);
  };

  // 删除公司
  const handleDeleteCompany = async (companyId) => {
    const company = selectedSubIndustry?.companies?.find((c) => c.id === companyId);
    if (!company) {
      alert('未找到公司信息');
      return;
    }
    if (!confirm(`确定删除 ${company.name} 吗？`)) return;

    try {
      const res = await fetchWithAuth(`${API_BASE}/companies/${companyId}`, {
        method: 'DELETE',
      });
      const data = await res.json();

      if (data.success) {
        await fetchIndustries();
      } else {
        alert(data.error || '删除失败');
      }
    } catch (e) {
      console.error('删除公司失败:', e);
      alert('删除失败');
    }
  };

  // 删除一级行业
  const handleDeleteIndustry = async (industry, e) => {
    e.stopPropagation();
    const totalCompanies = (industry.children || []).reduce(
      (sum, sub) => sum + (sub.companies?.length || 0),
      0
    );
    const msg =
      totalCompanies > 0
        ? `确定删除行业「${industry.name}」吗？该行业下有 ${totalCompanies} 家公司将一并删除。`
        : `确定删除行业「${industry.name}」吗？`;
    if (!confirm(msg)) return;

    try {
      const res = await fetchWithAuth(`${API_BASE}/industries/${industry.id}`, {
        method: 'DELETE',
      });
      const data = await res.json();

      if (data.success) {
        if (selectedIndustry?.id === industry.id) {
          setSelectedIndustry(null);
        }
        await fetchIndustries();
      } else {
        alert(data.error || '删除失败');
      }
    } catch (e) {
      console.error('删除行业失败:', e);
      alert('删除失败');
    }
  };

  // 删除子行业
  const handleDeleteSubIndustry = async (subIndustry, e) => {
    e.stopPropagation();
    const count = subIndustry.companies?.length || 0;
    const msg =
      count > 0
        ? `确定删除子行业「${subIndustry.name}」吗？该分类下有 ${count} 家公司将一并删除。`
        : `确定删除子行业「${subIndustry.name}」吗？`;
    if (!confirm(msg)) return;

    try {
      const res = await fetchWithAuth(`${API_BASE}/sub-industries/${subIndustry.id}`, {
        method: 'DELETE',
      });
      const data = await res.json();

      if (data.success) {
        if (selectedSubIndustry?.id === subIndustry.id) {
          setSelectedSubIndustry(null);
        }
        await fetchIndustries();
      } else {
        alert(data.error || '删除失败');
      }
    } catch (e) {
      console.error('删除子行业失败:', e);
      alert('删除失败');
    }
  };

  // 添加一级行业
  const handleAddIndustry = async () => {
    if (!newIndustry.name) {
      alert('请输入行业名称');
      return;
    }

    try {
      const res = await fetchWithAuth(`${API_BASE}/industries`, {
        method: 'POST',
        body: JSON.stringify({ name: newIndustry.name, icon: newIndustry.icon }),
      });
      const data = await res.json();

      if (data.success) {
        await fetchIndustries();
        setNewIndustry({ id: '', name: '', icon: '🏢', children: [] });
        setShowAddIndustryForm(false);
      } else {
        alert(data.error || '添加失败');
      }
    } catch (e) {
      console.error('添加行业失败:', e);
      alert('添加失败');
    }
  };

  // 编辑一级行业
  const handleEditIndustry = (industry, e) => {
    e.stopPropagation();
    setEditingIndustry(industry);
    setNewIndustry({ ...industry });
    setShowEditIndustryForm(true);
    setShowAddIndustryForm(false);
  };

  // 保存一级行业编辑
  const handleSaveIndustry = async () => {
    if (!newIndustry.name) {
      alert('请输入行业名称');
      return;
    }
    if (!editingIndustry) return;

    try {
      const res = await fetchWithAuth(`${API_BASE}/industries/${editingIndustry.id}`, {
        method: 'PUT',
        body: JSON.stringify({ name: newIndustry.name, icon: newIndustry.icon }),
      });
      const data = await res.json();

      if (data.success) {
        await fetchIndustries();
        setEditingIndustry(null);
        setNewIndustry({ id: '', name: '', icon: '🏢', children: [] });
        setShowEditIndustryForm(false);
      } else {
        alert(data.error || '更新失败');
      }
    } catch (e) {
      console.error('更新行业失败:', e);
      alert('更新失败');
    }
  };

  // 取消一级行业编辑
  const handleCancelIndustry = () => {
    setEditingIndustry(null);
    setNewIndustry({ id: '', name: '', icon: '🏢', children: [] });
    setShowEditIndustryForm(false);
  };

  // 添加子行业
  const handleAddSubIndustry = async () => {
    if (!newSubIndustry.name) {
      alert('请输入子行业名称');
      return;
    }
    if (!selectedIndustry) return;

    try {
      const res = await fetchWithAuth(`${API_BASE}/sub-industries`, {
        method: 'POST',
        body: JSON.stringify({ industry_id: selectedIndustry.id, name: newSubIndustry.name }),
      });
      const data = await res.json();

      if (data.success) {
        await fetchIndustries();
        setNewSubIndustry({ name: '', companies: [] });
        setShowAddSubForm(false);
      } else {
        alert(data.error || '添加失败');
      }
    } catch (e) {
      console.error('添加子行业失败:', e);
      alert('添加失败');
    }
  };

  // 编辑子行业
  const handleEditSubIndustry = (subIndustry, e) => {
    e.stopPropagation();
    setEditingSubIndustry({ ...subIndustry });
    setNewSubIndustry({ name: subIndustry.name, companies: [] });
    setShowEditSubForm(true);
    setShowAddSubForm(false);
  };

  // 保存子行业编辑
  const handleSaveSubIndustry = async () => {
    if (!newSubIndustry.name) {
      alert('请输入子行业名称');
      return;
    }
    if (!editingSubIndustry) return;

    try {
      const res = await fetchWithAuth(`${API_BASE}/sub-industries/${editingSubIndustry.id}`, {
        method: 'PUT',
        body: JSON.stringify({ name: newSubIndustry.name }),
      });
      const data = await res.json();

      if (data.success) {
        await fetchIndustries();
        setEditingSubIndustry(null);
        setNewSubIndustry({ name: '', companies: [] });
        setShowEditSubForm(false);
      } else {
        alert(data.error || '更新失败');
      }
    } catch (e) {
      console.error('更新子行业失败:', e);
      alert('更新失败');
    }
  };

  // 取消子行业编辑
  const handleCancelSubIndustry = () => {
    setEditingSubIndustry(null);
    setNewSubIndustry({ name: '', companies: [] });
    setShowEditSubForm(false);
  };

  // 搜索过滤
  const trimmedKeyword = searchKeyword.trim().toLowerCase();
  const isSearching = trimmedKeyword.length > 0;

  const filteredIndustries = isSearching
    ? industryData
        .map((industry) => {
          const industryMatch = industry.name.toLowerCase().includes(trimmedKeyword);
          const matchedChildren = (industry.children || [])
            .map((sub) => {
              const subMatch = sub.name.toLowerCase().includes(trimmedKeyword);
              if (subMatch || industryMatch) return sub;
              const matchedCompanies = (sub.companies || []).filter(
                (c) =>
                  c.name.toLowerCase().includes(trimmedKeyword) ||
                  c.code.toLowerCase().includes(trimmedKeyword)
              );
              return matchedCompanies.length > 0
                ? { ...sub, companies: matchedCompanies }
                : null;
            })
            .filter(Boolean);
          if (matchedChildren.length === 0) return null;
          return { ...industry, children: matchedChildren };
        })
        .filter(Boolean)
    : industryData;

  // 搜索模式下的扁平公司列表
  const searchResultCompanies = isSearching
    ? filteredIndustries.flatMap((industry) =>
        (industry.children || []).flatMap((sub) =>
          (sub.companies || []).map((c) => ({ ...c, industryName: industry.name, subName: sub.name }))
        )
      )
    : [];

  // 获取一级行业公司总数
  const getIndustryCompanyCount = (industry) =>
    (industry.children || []).reduce((sum, sub) => sum + (sub.companies?.length || 0), 0);

  // 当前选中行业的子行业列表
  const currentSubIndustries = selectedIndustry?.children || [];

  return (
    <div className="dao-page">
      {/* 左侧：行业分类树 */}
      <div className="dao-sidebar">
        <div className="dao-sidebar-header">
          <span>📊 行业分类</span>
          {canEdit && !showAddIndustryForm && !showEditIndustryForm && !isSearching && (
            <button
              className="btn-add-industry"
              onClick={() => {
                setShowAddIndustryForm(true);
                setShowEditIndustryForm(false);
                setShowAddSubForm(false);
                setShowEditSubForm(false);
              }}
            >
              + 添加行业
            </button>
          )}
        </div>
        <div className="dao-search-box">
          <input
            type="text"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            placeholder="🔍 搜索公司/代码/行业"
            className="dao-search-input"
          />
          {searchKeyword && (
            <button className="dao-search-clear" onClick={() => setSearchKeyword('')}>
              ✕
            </button>
          )}
        </div>
        <div className="dao-sidebar-content">
          {/* 添加行业表单 */}
          {canEdit && !isSearching && showAddIndustryForm && (
            <div className="industry-form">
              <input
                type="text"
                value={newIndustry.name}
                onChange={(e) => setNewIndustry({ ...newIndustry, name: e.target.value })}
                placeholder="输入行业名称"
                className="industry-input"
              />
              <input
                type="text"
                value={newIndustry.icon}
                onChange={(e) => setNewIndustry({ ...newIndustry, icon: e.target.value })}
                placeholder="行业图标（emoji）"
                className="industry-input icon-input"
              />
              <button className="btn btn-save-industry" onClick={handleAddIndustry}>
                ✓
              </button>
              <button
                className="btn btn-cancel-industry"
                onClick={() => {
                  setShowAddIndustryForm(false);
                  setNewIndustry({ id: '', name: '', icon: '🏢', children: [] });
                }}
              >
                ✕
              </button>
            </div>
          )}

          {filteredIndustries.length === 0 && isSearching && (
            <div className="dao-empty-state">未找到匹配的公司</div>
          )}

          {filteredIndustries.map((industry) => (
            <div key={industry.id} className="industry-group">
              {/* 编辑行业表单 */}
              {canEdit && !isSearching && showEditIndustryForm && editingIndustry?.id === industry.id && (
                <div className="industry-form edit-form">
                  <input
                    type="text"
                    value={newIndustry.name}
                    onChange={(e) => setNewIndustry({ ...newIndustry, name: e.target.value })}
                    placeholder="输入行业名称"
                    className="industry-input"
                  />
                  <input
                    type="text"
                    value={newIndustry.icon}
                    onChange={(e) => setNewIndustry({ ...newIndustry, icon: e.target.value })}
                    placeholder="行业图标"
                    className="industry-input icon-input"
                  />
                  <button className="btn btn-save-industry" onClick={handleSaveIndustry}>
                    ✓
                  </button>
                  <button className="btn btn-cancel-industry" onClick={handleCancelIndustry}>
                    ✕
                  </button>
                </div>
              )}

              <div
                className={`industry-item ${!isSearching && selectedIndustry?.id === industry.id ? 'active' : ''}`}
                onClick={() => selectIndustry(industry)}
              >
                <span className="industry-icon">{industry.icon}</span>
                <span className="industry-name">{industry.name}</span>
                <span className="industry-count-badge">{getIndustryCompanyCount(industry)}</span>
                <span className="industry-actions">
                  {canEdit && !isSearching && (
                    <>
                      <button
                        className="btn-edit-industry"
                        onClick={(e) => handleEditIndustry(industry, e)}
                      >
                        ✏️
                      </button>
                      <button
                        className="btn-delete-industry"
                        onClick={(e) => handleDeleteIndustry(industry, e)}
                      >
                        🗑️
                      </button>
                    </>
                  )}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 右侧：子行业分组平铺 */}
      <div className="dao-content">
        <div className="dao-content-header">
          <h2>
            {isSearching
              ? `搜索结果：${searchResultCompanies.length} 家公司`
              : selectedIndustry
              ? `${selectedIndustry.icon} ${selectedIndustry.name}`
              : '请选择行业分类'}
          </h2>
          {!isSearching && selectedIndustry && canEdit && (
            <div style={{ display: 'flex', gap: '8px' }}>
              {selectedSubIndustry && (
                <button
                  className="btn btn-add-company"
                  onClick={() => startAddCompany()}
                >
                  + 添加公司
                </button>
              )}
              <button
                className="btn btn-add-sub-inline"
                onClick={() => {
                  setShowAddSubForm(!showAddSubForm);
                  setShowEditSubForm(false);
                }}
              >
                {showAddSubForm ? '取消' : '+ 添加子分类'}
              </button>
            </div>
          )}
        </div>

        {/* 添加子行业表单 */}
        {canEdit && !isSearching && showAddSubForm && (
          <div className="sub-industry-form-inline">
            <input
              type="text"
              value={newSubIndustry.name}
              onChange={(e) => setNewSubIndustry({ ...newSubIndustry, name: e.target.value })}
              placeholder="输入子行业名称"
              className="sub-industry-input"
            />
            <button className="btn btn-primary" onClick={handleAddSubIndustry}>
              确认添加
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => {
                setShowAddSubForm(false);
                setNewSubIndustry({ name: '', companies: [] });
              }}
            >
              取消
            </button>
          </div>
        )}

        {/* 编辑子行业表单 */}
        {canEdit && !isSearching && showEditSubForm && editingSubIndustry && (
          <div className="sub-industry-form-inline edit">
            <input
              type="text"
              value={newSubIndustry.name}
              onChange={(e) => setNewSubIndustry({ ...newSubIndustry, name: e.target.value })}
              placeholder="输入子行业名称"
              className="sub-industry-input"
            />
            <button className="btn btn-primary" onClick={handleSaveSubIndustry}>
              确认修改
            </button>
            <button className="btn btn-secondary" onClick={handleCancelSubIndustry}>
              取消
            </button>
          </div>
        )}

        {/* 编辑公司表单 */}
        {canEdit && !isSearching && showEditForm && (
          <div className="add-company-form edit-form">
            <div className="form-header">
              <h3>编辑公司</h3>
              <button className="btn-close" onClick={handleCancelEdit}>
                ✕
              </button>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>公司代码 *</label>
                <input
                  type="text"
                  value={newCompany.code}
                  onChange={(e) => setNewCompany({ ...newCompany, code: e.target.value })}
                  placeholder="如: 300394"
                />
              </div>
              <div className="form-group">
                <label>公司名称 *</label>
                <input
                  type="text"
                  value={newCompany.name}
                  onChange={(e) => setNewCompany({ ...newCompany, name: e.target.value })}
                  placeholder="如: 天孚通信"
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group full-width">
                <label>所属子分类 *</label>
                <select
                  value={newCompany.sub_industry_id || ''}
                  onChange={(e) => setNewCompany({ ...newCompany, sub_industry_id: e.target.value })}
                >
                  {currentSubIndustries.map((sub) => (
                    <option key={sub.id} value={sub.id}>{sub.name}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>行业地位</label>
                <input
                  type="text"
                  value={newCompany.role}
                  onChange={(e) => setNewCompany({ ...newCompany, role: e.target.value })}
                  placeholder="如: 光模块龙头"
                />
              </div>
              <div className="form-group">
                <label>主营业务</label>
                <input
                  type="text"
                  value={newCompany.desc}
                  onChange={(e) => setNewCompany({ ...newCompany, desc: e.target.value })}
                  placeholder="如: 光模块产品研发制造"
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group full-width">
                <label>核心特征</label>
                <textarea
                  value={newCompany.feature}
                  onChange={(e) => setNewCompany({ ...newCompany, feature: e.target.value })}
                  placeholder="如: 800G/1.6T高速光模块量产能力，绑定头部客户"
                  rows="2"
                />
              </div>
            </div>
            <div className="form-actions">
              <button className="btn btn-primary" onClick={handleSaveEdit}>
                确认修改
              </button>
              <button className="btn btn-secondary" onClick={handleCancelEdit}>
                取消
              </button>
            </div>
          </div>
        )}

        {/* 添加公司表单 */}
        {canEdit && !isSearching && showAddForm && (
          <div className="add-company-form">
            <div className="form-header">
              <h3>添加公司</h3>
              <button className="btn-close" onClick={() => { setShowAddForm(false); setAddCompanySubId(null); }}>
                ✕
              </button>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>公司代码 *</label>
                <input
                  type="text"
                  value={newCompany.code}
                  onChange={(e) => setNewCompany({ ...newCompany, code: e.target.value })}
                  placeholder="如: 300394"
                />
              </div>
              <div className="form-group">
                <label>公司名称 *</label>
                <input
                  type="text"
                  value={newCompany.name}
                  onChange={(e) => setNewCompany({ ...newCompany, name: e.target.value })}
                  placeholder="如: 天孚通信"
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>行业地位</label>
                <input
                  type="text"
                  value={newCompany.role}
                  onChange={(e) => setNewCompany({ ...newCompany, role: e.target.value })}
                  placeholder="如: 光模块龙头"
                />
              </div>
              <div className="form-group">
                <label>主营业务</label>
                <input
                  type="text"
                  value={newCompany.desc}
                  onChange={(e) => setNewCompany({ ...newCompany, desc: e.target.value })}
                  placeholder="如: 光模块产品研发制造"
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group full-width">
                <label>核心特征</label>
                <textarea
                  value={newCompany.feature}
                  onChange={(e) => setNewCompany({ ...newCompany, feature: e.target.value })}
                  placeholder="如: 800G/1.6T高速光模块量产能力，绑定头部客户"
                  rows="2"
                />
              </div>
            </div>
            <div className="form-actions">
              <button className="btn btn-primary" onClick={handleAddCompany}>
                确认添加
              </button>
              <button className="btn btn-secondary" onClick={() => { setShowAddForm(false); setAddCompanySubId(null); }}>
                取消
              </button>
            </div>
          </div>
        )}

        <div className="dao-content-body">
          {isSearching ? (
            <div className="company-grid">
              {searchResultCompanies.length === 0 ? (
                <div className="dao-empty-state">未找到匹配的公司</div>
              ) : (
                searchResultCompanies.map((company) => (
                  <div key={company.code} className="company-card-wrapper">
                    <div className="company-card-source">
                      {company.industryName} / {company.subName}
                    </div>
                    <CompanyCard
                      company={company}
                      onSelect={handleCompanySelect}
                      onEdit={handleEditCompany}
                      onDelete={handleDeleteCompany}
                    />
                  </div>
                ))
              )}
            </div>
          ) : !selectedIndustry ? (
            <div className="dao-empty-state">请选择左侧行业分类查看公司</div>
          ) : currentSubIndustries.length === 0 ? (
            <div className="dao-empty-state">
              该行业暂无子分类，点击右上角「+ 添加子分类」开始录入
            </div>
          ) : (
            <>
              {/* 子分类 Tab 平铺 */}
              <div className="sub-industry-tabs">
                {currentSubIndustries.map((sub) => (
                  <div
                    key={sub.id}
                    className={`sub-industry-tab ${selectedSubIndustry?.id === sub.id ? 'active' : ''}`}
                    onClick={() => selectSubIndustry(sub)}
                  >
                    <span className="sub-industry-tab-name">{sub.name}</span>
                    <span className="sub-industry-tab-count">{sub.companies?.length || 0}</span>
                    {canEdit && selectedSubIndustry?.id === sub.id && (
                      <span className="sub-industry-tab-actions">
                        <button
                          className="btn-edit-sub"
                          onClick={(e) => handleEditSubIndustry(sub, e)}
                        >
                          ✏️
                        </button>
                        <button
                          className="btn-delete-sub"
                          onClick={(e) => handleDeleteSubIndustry(sub, e)}
                        >
                          🗑️
                        </button>
                      </span>
                    )}
                  </div>
                ))}
              </div>

              {/* 选中子分类的公司卡片 */}
              {selectedSubIndustry ? (
                <div className="company-grid">
                  {(selectedSubIndustry.companies || []).length === 0 ? (
                    <div className="dao-empty-state">
                      {canEdit
                        ? '该分类暂无公司，点击「+ 添加公司」录入'
                        : '该分类暂无公司'}
                    </div>
                  ) : (
                    selectedSubIndustry.companies.map((company) => (
                      <div key={company.code} className="company-card-wrapper">
                        <CompanyCard
                          company={company}
                          onSelect={handleCompanySelect}
                          onEdit={handleEditCompany}
                          onDelete={handleDeleteCompany}
                        />
                      </div>
                    ))
                  )}
                </div>
              ) : (
                <div className="dao-empty-state">请选择上方子分类查看公司</div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default DaoPage;
