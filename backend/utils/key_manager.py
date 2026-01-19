"""
密钥管理工具
"""
import os
import json
import base64
from pygroupsig import groupsig, constants, grpkey, mgrkey, memkey, gml, crl, signature

class KeyManager:
    """密钥管理器"""
    
    def __init__(self):
        self.code = constants.KTY04_CODE
        self.data_dir = 'data'
        self.groups_dir = os.path.join(self.data_dir, 'groups')
        self.members_dir = os.path.join(self.data_dir, 'members')
        
        # 确保目录存在
        os.makedirs(self.groups_dir, exist_ok=True)
        os.makedirs(self.members_dir, exist_ok=True)
    
    def init_scheme(self):
        """初始化 KTY04 方案"""
        groupsig.init(self.code, 0)
    
    def clear_scheme(self):
        """清理 KTY04 方案"""
        groupsig.clear(self.code)
    
    def save_group_keys(self, group_id, grpkey_obj, mgrkey_obj, gml_obj):
        """保存群组密钥"""
        group_dir = os.path.join(self.groups_dir, str(group_id))
        os.makedirs(group_dir, exist_ok=True)
        
        # 导出密钥
        grpkey_str = grpkey.grpkey_export(grpkey_obj)
        mgrkey_str = mgrkey.mgrkey_export(mgrkey_obj)
        gml_str = gml.gml_export(gml_obj)
        
        # 保存到文件
        with open(os.path.join(group_dir, 'grpkey.json'), 'w') as f:
            json.dump({'data': grpkey_str}, f)
        
        with open(os.path.join(group_dir, 'mgrkey.json'), 'w') as f:
            json.dump({'data': mgrkey_str}, f)
        
        with open(os.path.join(group_dir, 'gml.json'), 'w') as f:
            json.dump({'data': gml_str}, f)
        
        return {
            'grpkey_path': os.path.join(group_dir, 'grpkey.json'),
            'mgrkey_path': os.path.join(group_dir, 'mgrkey.json'),
            'gml_path': os.path.join(group_dir, 'gml.json')
        }
    
    def load_group_keys(self, group_id):
        """加载群组密钥"""
        group_dir = os.path.join(self.groups_dir, str(group_id))
        
        with open(os.path.join(group_dir, 'grpkey.json'), 'r') as f:
            grpkey_data = json.load(f)['data']
        
        with open(os.path.join(group_dir, 'mgrkey.json'), 'r') as f:
            mgrkey_data = json.load(f)['data']
        
        with open(os.path.join(group_dir, 'gml.json'), 'r') as f:
            gml_data = json.load(f)['data']
        
        grpkey_obj = grpkey.grpkey_import(self.code, grpkey_data)
        mgrkey_obj = mgrkey.mgrkey_import(self.code, mgrkey_data)
        gml_obj = gml.gml_import(self.code, gml_data)
        
        return grpkey_obj, mgrkey_obj, gml_obj
    
    def save_member_key(self, group_id, member_id, memkey_obj):
        """保存成员密钥"""
        member_dir = os.path.join(self.members_dir, f"{group_id}_{member_id}")
        os.makedirs(member_dir, exist_ok=True)
        
        memkey_str = memkey.memkey_export(memkey_obj)
        
        with open(os.path.join(member_dir, 'memkey.json'), 'w') as f:
            json.dump({'data': memkey_str}, f)
        
        return os.path.join(member_dir, 'memkey.json')
    
    def load_member_key(self, group_id, member_id):
        """加载成员密钥"""
        member_dir = os.path.join(self.members_dir, f"{group_id}_{member_id}")
        
        with open(os.path.join(member_dir, 'memkey.json'), 'r') as f:
            memkey_data = json.load(f)['data']
        
        return memkey.memkey_import(self.code, memkey_data)
    
    def save_signature(self, sig_obj, message_text):
        """保存签名"""
        sig_str = signature.signature_export(sig_obj)
        return sig_str
    
    def load_signature(self, sig_data):
        """加载签名"""
        return signature.signature_import(self.code, sig_data)
