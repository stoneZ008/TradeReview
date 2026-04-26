import React from 'react';

function CompanyCard({ company, onSelect, onEdit }) {
  const handleEdit = (e) => {
    e.stopPropagation();
    if (onEdit) {
      onEdit(company);
    }
  };

  return (
    <div className="company-card" onClick={() => onSelect(company)}>
      <div className="company-header">
        <span className="company-code">{company.code}</span>
        <span className="company-name">{company.name}</span>
      </div>
      <div className="company-role">{company.role}</div>
      <div className="company-feature">{company.feature}</div>
      <div className="company-desc">{company.desc}</div>
      <div className="company-action">
        <span className="view-kline">📈 查看K线</span>
        <button className="btn-edit-company" onClick={handleEdit}>
          ✏️ 编辑
        </button>
      </div>
    </div>
  );
}

export default CompanyCard;
