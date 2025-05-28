print('Starting MongoDB initialization...');

try {
    // Create admin user if it doesn't exist
    db.createUser({
        user: process.env.MONGO_INITDB_ROOT_USERNAME || 'admin',
        pwd: process.env.MONGO_INITDB_ROOT_PASSWORD || 'adminpassword',
        roles: [
            { role: "readWrite", db: process.env.MONGO_INITDB_DATABASE || 'company_research' },
            { role: "dbAdmin", db: process.env.MONGO_INITDB_DATABASE || 'company_research' }
        ]
    });

    print('User created successfully');
} catch (err) {
    print('Error creating user (might already exist): ' + err.message);
}

// Switch to the application database
db = db.getSiblingDB(process.env.MONGO_INITDB_DATABASE || 'company_research');
print('Switched to database: ' + db.getName());

// Create collections
['companies', 'research_tasks'].forEach(function(collection) {
    try {
        db.createCollection(collection);
        print('Created collection: ' + collection);
    } catch (err) {
        print('Error creating collection ' + collection + ' (might already exist): ' + err.message);
    }
});

// Create indexes
try {
    db.companies.createIndex({ "name": 1 }, { 
        unique: true,
        background: true
    });
    print('Created index on companies.name');
} catch (err) {
    print('Error creating companies index: ' + err.message);
}

try {
    db.research_tasks.createIndex({ "status": 1 }, { background: true });
    print('Created index on research_tasks.status');
} catch (err) {
    print('Error creating status index: ' + err.message);
}

try {
    db.research_tasks.createIndex({ "created_at": 1 }, { background: true });
    print('Created index on research_tasks.created_at');
} catch (err) {
    print('Error creating created_at index: ' + err.message);
}

print('MongoDB initialization completed'); 