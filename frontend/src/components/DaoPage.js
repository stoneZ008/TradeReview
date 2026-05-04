import React, { useState, useEffect } from 'react';
import CompanyCard from './CompanyCard';
import { useAuth } from '../context/AuthContext';
import { API_BASE, fetchWithAuth } from '../api';

function DaoPage({ onStockSelect }) {
  const { hasRole } = useAuth();
  const canEdit = hasRole('admin') || hasRole('super_admin');
  const [industryData, setIndustryData] = useState([]);
  const [expandedIndustries, setExpandedIndustries] = useState([]);
  const [selectedSubIndustry, setSelectedSubIndustry] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editingCompany, setEditingCompany] = useState(null);
  const [newCompany, setNewCompany] = useState({
    code: '',
    name: '',
    role: '',
    feature: '',
    desc: ''
  });
  
  // 子行业表单状态
  const [showAddSubForm, setShowAddSubForm] = useState(false);
  const [showEditSubForm, setShowEditSubForm] = useState(false);
  const [editingSubIndustry, setEditingSubIndustry] = useState(null);
  const [selectedIndustryId, setSelectedIndustryId] = useState(null);
  const [newSubIndustry, setNewSubIndustry] = useState({
    name: '',
    companies: []
  });
  
  // 一级行业表单状态
  const [showAddIndustryForm, setShowAddIndustryForm] = useState(false);
  const [showEditIndustryForm, setShowEditIndustryForm] = useState(false);
  const [editingIndustry, setEditingIndustry] = useState(null);
  const [newIndustry, setNewIndustry] = useState({
    id: '',
    name: '',
    icon: '🏢',
    children: []
  });

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
        // 展开第一个行业
        if (data.data.length > 0) {
          setExpandedIndustries([data.data[0].id]);
        }
        // 更新当前选中的子行业数据
        if (selectedSubIndustry) {
          for (const industry of data.data) {
            const found = industry.children.find(sub => sub.id === selectedSubIndustry.id);
            if (found) {
              setSelectedSubIndustry(found);
              break;
            }
          }
        }
      }
    } catch (e) {
      console.error('加载行业数据失败:', e);
    }
  };

  // 切换行业展开/折叠
  const toggleIndustry = (industryId) => {
    setExpandedIndustries(prev => 
      prev.includes(industryId) 
        ? prev.filter(id => id !== industryId)
        : [...prev, industryId]
    );
  };

  // 选择子行业
  const selectSubIndustry = (subIndustry) => {
    setSelectedSubIndustry(subIndustry);
    setShowAddForm(false);
  };

  // 点击公司卡片
  const handleCompanySelect = (company) => {
    if (onStockSelect) {
      onStockSelect(company.code);
    }
  };

  // 获取当前选中的公司列表
  const getCurrentCompanies = () => {
    if (!selectedSubIndustry) return [];
    return selectedSubIndustry.companies || [];
  };

  // 添加公司
  const handleAddCompany = async () => {
    if (!newCompany.code || !newCompany.name) {
      alert('请填写公司代码和名称');
      return;
    }
    if (!selectedSubIndustry) {
      alert('请先选择一个行业分类');
      return;
    }

    try {
      const res = await fetchWithAuth(`${API_BASE}/companies`, {
        method: 'POST',
        body: JSON.stringify({
          sub_industry_id: selectedSubIndustry.id,
          code: newCompany.code,
          name: newCompany.name,
          role: newCompany.role,
          feature: newCompany.feature,
          description: newCompany.desc
        })
      });
      const data = await res.json();
      
      if (data.success) {
        await fetchIndustries();
        setNewCompany({ code: '', name: '', role: '', feature: '', desc: '' });
        setShowAddForm(false);
        setSelectedSubIndustry(null);
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
          description: newCompany.desc
        })
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
    const company = selectedSubIndustry?.companies?.find(c => c.id === companyId);
    if (!company) {
      alert('未找到公司信息');
      return;
    }
    if (!confirm(`确定删除 ${company.name} 吗？`)) return;

    try {
      const res = await fetchWithAuth(`${API_BASE}/companies/${companyId}`, {
        method: 'DELETE'
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

  // 添加一级行业
  const handleAddIndustry = async () => {
    if (!newIndustry.name) {
      alert('请输入行业名称');
      return;
    }

    try {
      const res = await fetchWithAuth(`${API_BASE}/industries`, {
        method: 'POST',
        body: JSON.stringify({ name: newIndustry.name, icon: newIndustry.icon })
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
        body: JSON.stringify({ name: newIndustry.name, icon: newIndustry.icon })
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
  const handleAddSubIndustry = async (industryId) => {
    if (!newSubIndustry.name) {
      alert('请输入子行业名称');
      return;
    }

    try {
      const res = await fetchWithAuth(`${API_BASE}/sub-industries`, {
        method: 'POST',
        body: JSON.stringify({ industry_id: industryId, name: newSubIndustry.name })
      });
      const data = await res.json();
      
      if (data.success) {
        await fetchIndustries();
        setNewSubIndustry({ name: '', companies: [] });
        setShowAddSubForm(false);
        
        // 展开该行业
        if (!expandedIndustries.includes(industryId)) {
          setExpandedIndustries([...expandedIndustries, industryId]);
        }
      } else {
        alert(data.error || '添加失败');
      }
    } catch (e) {
      console.error('添加子行业失败:', e);
      alert('添加失败');
    }
  };

  // 编辑子行业
  const handleEditSubIndustry = (industryId, subIndustry, e) => {
    e.stopPropagation();
    setEditingSubIndustry({ ...subIndustry, industryId });
    setNewSubIndustry({ name: subIndustry.name, companies: [] });
    setShowEditSubForm(true);
    setShowAddSubForm(false);
    setSelectedIndustryId(industryId);
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
        body: JSON.stringify({ name: newSubIndustry.name })
      });
      const data = await res.json();
      
      if (data.success) {
        await fetchIndustries();
        
        // 更新选中的子行业
        if (selectedSubIndustry?.id === editingSubIndustry.id) {
          setSelectedSubIndustry({
            ...selectedSubIndustry,
            name: newSubIndustry.name
          });
        }
        
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

  return (
    <div className="dao-page">
      {/* 左侧：行业分类树 */}
      <div className="dao-sidebar">
        <div className="dao-sidebar-header">
          <span>📊 行业分类</span>
          {canEdit && !showAddIndustryForm && !showEditIndustryForm && (
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
        <div className="dao-sidebar-content">
           {/* 添加行业表单 */}
           {canEdit && showAddIndustryForm && (
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
              <button 
                className="btn btn-save-industry"
                onClick={handleAddIndustry}
              >
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

          {industryData.map(industry => (
            <div key={industry.id} className="industry-group">
               {/* 编辑行业表单 */}
               {canEdit && showEditIndustryForm && editingIndustry?.id === industry.id && (
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
                  <button 
                    className="btn btn-save-industry"
                    onClick={handleSaveIndustry}
                  >
                    ✓
                  </button>
                  <button 
                    className="btn btn-cancel-industry"
                    onClick={handleCancelIndustry}
                  >
                    ✕
                  </button>
                </div>
              )}

              <div 
                className={`industry-item ${expandedIndustries.includes(industry.id) ? 'expanded' : ''}`}
                onClick={() => toggleIndustry(industry.id)}
              >
                <span className="industry-icon">{industry.icon}</span>
                <span className="industry-name">{industry.name}</span>
                <span className="industry-actions">
                  <span className="industry-arrow">
                    {expandedIndustries.includes(industry.id) ? '▼' : '▶'}
                  </span>
                  {canEdit && (
                    <button 
                      className="btn-edit-industry"
                      onClick={(e) => handleEditIndustry(industry, e)}
                    >
                      ✏️
                    </button>
                  )}
                </span>
              </div>
              
              {expandedIndustries.includes(industry.id) && (
                <div className="sub-industry-list">
                  {industry.children.map(sub => (
                    <div 
                      key={sub.id}
                      className={`sub-industry-item ${selectedSubIndustry?.id === sub.id ? 'active' : ''}`}
                      onClick={() => selectSubIndustry(sub)}
                    >
                      <span className="sub-industry-name">{sub.name}</span>
                      <span className="sub-industry-actions">
                        <span className="sub-industry-count">{sub.companies?.length || 0}</span>
                        {canEdit && (
                          <button 
                            className="btn-edit-sub"
                            onClick={(e) => handleEditSubIndustry(industry.id, sub, e)}
                          >
                            ✏️
                          </button>
                        )}
                      </span>
                    </div>
                  ))}
                  
                   {/* 添加子行业按钮 */}
                   {canEdit && showAddSubForm && selectedIndustryId === industry.id && (
                     <div className="sub-industry-form">
                      <input
                        type="text"
                        value={newSubIndustry.name}
                        onChange={(e) => setNewSubIndustry({ ...newSubIndustry, name: e.target.value })}
                        placeholder="输入子行业名称"
                        className="sub-industry-input"
                      />
                      <button 
                        className="btn btn-save-sub"
                        onClick={() => handleAddSubIndustry(industry.id)}
                      >
                        ✓
                      </button>
                      <button 
                        className="btn btn-cancel-sub"
                        onClick={() => {
                          setShowAddSubForm(false);
                          setNewSubIndustry({ name: '', companies: [] });
                        }}
                      >
                        ✕
                      </button>
                    </div>
                  )}
                  
                   {canEdit && !(showAddSubForm && selectedIndustryId === industry.id) && (
                     <button 
                       className="btn-add-sub"
                       onClick={(e) => {
                         e.stopPropagation();
                         setSelectedIndustryId(industry.id);
                         setShowAddSubForm(true);
                         setShowEditSubForm(false);
                       }}
                     >
                       + 添加子分类
                     </button>
                   )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 右侧：公司卡片列表 */}
      <div className="dao-content">
        <div className="dao-content-header">
          <h2>
            {selectedSubIndustry 
              ? `${selectedSubIndustry.name} 龙头公司`
              : '请选择行业分类'
            }
          </h2>
          {selectedSubIndustry && canEdit && (
            <button 
              className="btn btn-add-company"
              onClick={() => setShowAddForm(!showAddForm)}
            >
              {showAddForm ? '取消' : '+ 添加公司'}
            </button>
          )}
        </div>

        {/* 编辑公司表单 */}
        {canEdit && showEditForm && (
          <div className="add-company-form edit-form">
            <div className="form-header">
              <h3>编辑公司</h3>
              <button className="btn-close" onClick={handleCancelEdit}>✕</button>
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
        {canEdit && showAddForm && (
          <div className="add-company-form">
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
              <button className="btn btn-secondary" onClick={() => setShowAddForm(false)}>
                取消
              </button>
            </div>
          </div>
        )}

         <div className="dao-content-body">
           <div className="company-grid">
             {getCurrentCompanies().map(company => (
               <div key={company.code} className="company-card-wrapper">
                 <CompanyCard 
                   company={company}
                   onSelect={handleCompanySelect}
                   onEdit={handleEditCompany}
                   onDelete={handleDeleteCompany}
                 />
               </div>
             ))}
           </div>
         </div>
      </div>
    </div>
  );
}

export default DaoPage;
