import React from 'react';
import { useAuth } from '../context/AuthContext';

function CompanyCard({ company, onSelect, onEdit, onDelete }) {
  const { hasRole } = useAuth();
  const canEdit = hasRole('admin') || hasRole('super_admin');

  const handleEdit = (e) => {
    e.stopPropagation();
    if (onEdit) {
      onEdit(company);
    }
  };

  const handleDelete = (e) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(company.id);
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
        {canEdit && (
          <>
            <button className="btn-edit-company" onClick={handleEdit}>
              ✏️ 编辑
            </button>
            <button className="btn-delete-company" onClick={handleDelete}>
              🗑️ 删除
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default CompanyCard;
