# API VERSIONING SYSTEM

class APIVersionManager:
    def __init__(self):
        self.versions = {}
        self.current_version = "v1"
    
    def register_version(self, version, routes):
        self.versions[version] = routes
        print(f"✅ API version registered: {version}")
    
    def get_version(self, version):
        return self.versions.get(version, self.versions.get(self.current_version))
    
    def deprecate_version(self, version, sunset_date):
        print(f"⚠️ API version {version} will be deprecated on {sunset_date}")
