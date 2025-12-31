# 📊 Kibana Guide - Elasticsearch Monitoring

## 🎯 Overview

Kibana is included in the Docker Compose setup to provide powerful visualization and monitoring capabilities for the Elasticsearch data.

---

## 🚀 Accessing Kibana

Once your Docker services are running:

```bash
# Start services
docker-compose up -d

# Access Kibana
xdg-open http://localhost:5601
```

**URL:** http://localhost:5601

---

## 📋 What You Can Do with Kibana

### **1. Discover - Browse Your News Data**

Navigate to **Discover** to:
- Browse all cybersecurity news articles stored in Elasticsearch
- Search using Elasticsearch query syntax
- Filter by source, date, keywords
- View document details

### **2. Dev Tools - Query Console**

Use **Dev Tools > Console** to run queries:

```json
# Get all documents
GET cybersecurity_news/_search
{
  "query": {
    "match_all": {}
  }
}

# Search for specific terms
GET cybersecurity_news/_search
{
  "query": {
    "match": {
      "title": "ransomware"
    }
  }
}

# Get document count
GET cybersecurity_news/_count

# Get index mapping
GET cybersecurity_news/_mapping

# Get index settings
GET cybersecurity_news/_settings
```

### **3. Dashboard - Create Visualizations**

Create custom dashboards to visualize:
- News volume over time
- Most active sources
- Trending topics
- Publication patterns

### **4. Index Management**

Monitor and manage the `cybersecurity_news` index:
- View document count
- Check index health
- Manage aliases
- Configure settings

---

## 🔍 Useful Queries

### **Check Index Stats**

```json
GET cybersecurity_news/_stats
```

### **Get Recent News**

```json
GET cybersecurity_news/_search
{
  "query": {
    "range": {
      "published": {
        "gte": "now-24h"
      }
    }
  },
  "sort": [
    {
      "published": {
        "order": "desc"
      }
    }
  ]
}
```

### **Count by Source**

```json
GET cybersecurity_news/_search
{
  "size": 0,
  "aggs": {
    "sources": {
      "terms": {
        "field": "source.keyword",
        "size": 10
      }
    }
  }
}
```

### **Search in Title and Description**

```json
GET cybersecurity_news/_search
{
  "query": {
    "multi_match": {
      "query": "vulnerability",
      "fields": ["title", "description"]
    }
  }
}
```

---

## 📊 Creating a Simple Dashboard

### **Step 1: Create Data View**

1. Go to **Stack Management** > **Data Views**
2. Click **Create data view**
3. Name: `Cybersecurity News`
4. Index pattern: `cybersecurity_news`
5. Timestamp field: `published`
6. Click **Create**

### **Step 2: Create Visualizations**

1. Go to **Visualize Library**
2. Click **Create visualization**
3. Choose visualization type (e.g., Bar chart, Line chart, Pie chart)
4. Select your data view
5. Configure visualization

**Example - News by Source:**
- Visualization: Pie chart
- Metric: Count
- Buckets: Terms aggregation on `source.keyword`

**Example - News Over Time:**
- Visualization: Line chart
- Metric: Count
- X-axis: Date histogram on `published`

### **Step 3: Create Dashboard**

1. Go to **Dashboard**
2. Click **Create dashboard**
3. Add your visualizations
4. Save dashboard

---

## 🛠️ Configuration

### **Current Settings (from docker-compose.yml)**

```yaml
kibana:
  image: kibana:8.15.2
  ports:
    - '5601:5601'
  environment:
    - xpack.security.enabled=false
  depends_on:
    - elasticsearch
```

### **Environment Variables**

- `xpack.security.enabled=false` - Security disabled for development
- Automatically connects to Elasticsearch on default port

---

## 🔧 Troubleshooting

### **Kibana Not Loading**

```bash
# Check container status
docker-compose ps kibana

# Check logs
docker-compose logs kibana

# Restart Kibana
docker-compose restart kibana
```

### **"Unable to retrieve version information"**

Wait for Elasticsearch to be fully started:

```bash
# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# Should return: "status":"green" or "status":"yellow"
```

### **Port 5601 Already in Use**

```bash
# Find process
lsof -i :5601

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

---

## 📚 Learn More

- **Kibana Documentation:** https://www.elastic.co/guide/en/kibana/current/index.html
- **Query DSL:** https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html
- **Visualizations:** https://www.elastic.co/guide/en/kibana/current/dashboard.html

---

## 💡 Tips

1. **Use Dev Tools** for quick data inspection and debugging
2. **Create saved searches** for frequently used queries
3. **Build dashboards** to monitor news trends
4. **Use filters** to narrow down results quickly
5. **Export visualizations** to share with your team

---

**Kibana provides powerful tools to explore and visualize your cybersecurity news data! 📊**


