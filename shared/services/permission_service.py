class PermissionService:
    def __init__(self, current_user=None):
        self.current_user = current_user
        
        self.role_permissions = {
            '管理员': [
                'product.view', 'product.edit', 'product.delete',
                'purchase.view', 'purchase.edit', 'purchase.delete',
                'stock.view', 'stock.edit',
                'sale.view', 'sale.edit',
                'member.view', 'member.edit', 'member.delete',
                'finance.view', 'finance.edit',
                'system.view', 'system.edit'
            ],
            '收银员': [
                'sale.view', 'sale.edit',
                'product.view',
                'member.view'
            ],
            '采购员': [
                'purchase.view', 'purchase.edit',
                'product.view',
                'supplier.view', 'supplier.edit'
            ],
            '库管员': [
                'stock.view', 'stock.edit',
                'product.view',
                'purchase.view'
            ]
        }
    
    def has_permission(self, permission):
        if not self.current_user:
            return False
        
        role = self.current_user.role
        permissions = self.role_permissions.get(role, [])
        return permission in permissions
    
    def check_permission(self, permission):
        if not self.has_permission(permission):
            raise PermissionError(f"权限不足: {permission}")
    
    def can_view_product(self):
        return self.has_permission('product.view')
    
    def can_edit_product(self):
        return self.has_permission('product.edit')
    
    def can_delete_product(self):
        return self.has_permission('product.delete')
    
    def can_view_purchase(self):
        return self.has_permission('purchase.view')
    
    def can_edit_purchase(self):
        return self.has_permission('purchase.edit')
    
    def can_view_sale(self):
        return self.has_permission('sale.view')
    
    def can_edit_sale(self):
        return self.has_permission('sale.edit')
    
    def can_view_member(self):
        return self.has_permission('member.view')
    
    def can_edit_member(self):
        return self.has_permission('member.edit')
    
    def can_view_finance(self):
        return self.has_permission('finance.view')
    
    def can_edit_finance(self):
        return self.has_permission('finance.edit')
