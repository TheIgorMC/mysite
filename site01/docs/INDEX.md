# Documentation Index

Welcome to the Archery Analysis System documentation! This folder contains all technical documentation, guides, and references.

## 📚 Quick Navigation

### Getting Started
- [Project README](README.md) - Main project information
- [Quick Start Guide](QUICK_START.txt) - Get up and running quickly
- [Setup Guide](SETUP_GUIDE.md) - Detailed installation instructions
- [Project Summary](PROJECT_SUMMARY.md) - Complete project summary
- [Project Overview](OVERVIEW.md) - High-level overview

### Architecture & Design
- [System Architecture](ARCHITECTURE.md) - Overall system design
- [Project Specifications](specifications.md) - Original project requirements
- [File Index](FILE_INDEX.md) - Complete file structure reference

### Features Documentation
- **[Statistics Features](features/statistics.md)** - Career vs filtered stats, multi-athlete comparison
- **[Statistics Quick Reference](features/statistics-quick-reference.md)** - Quick usage guide
- **[Statistics Summary](features/statistics-summary.md)** - Implementation details
- **[Date Handling](features/date-handling.md)** - Date normalization system
- **[Date Fix Summary](features/date-fix-summary.md)** - Date handling improvements
- **[Loading States](features/loading-states.md)** - Loading indicators implementation
- [Archery Analysis Features](ARCHERY_ANALYSIS_FEATURES.md) - Complete feature list

### API Documentation
- **[API Usage Guide](api/usage-guide.md)** - How to use the Orion API
- **[API Specification](api/spec.json)** - OpenAPI 3.1 specification

### Implementation Documentation
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Latest updates and changes

## 🎯 Feature Highlights

### Advanced Statistics
The system provides comprehensive statistics with:
- **Dual View**: Career statistics + Filtered period statistics
- **Comparison Mode**: Compare up to 5 athletes side-by-side
- **Dynamic Updates**: Auto-refresh when athletes added/removed
- **Flexible Filters**: Date range, competition type, category
- **Loading Indicators**: Visual feedback during API calls

**Learn more:** [Statistics Features](features/statistics.md)

### Date Handling
Robust date processing ensuring:
- Support for multiple date formats
- Proper chronological ordering
- Accurate athlete comparisons
- Reliable statistics calculations

**Learn more:** [Date Handling Guide](features/date-handling.md)

### API Integration
Secure integration with Orion API via:
- Cloudflare Access authentication
- HTTPS connection (api.orion-project.it:443)
- CSV-based local filtering
- Proper error handling
- Loading states for all API calls

**Learn more:** [API Usage Guide](api/usage-guide.md)

## 📖 Documentation by Role

### For Developers
1. Start with [System Architecture](ARCHITECTURE.md)
2. Review [API Usage Guide](api/usage-guide.md)
3. Understand [Date Handling](features/date-handling.md)
4. Check [File Index](FILE_INDEX.md) for code structure

### For Users/Athletes
1. Start with [Quick Start](QUICK_START.txt)
2. Use [Statistics Quick Reference](features/statistics-quick-reference.md)
3. Learn about [Archery Analysis Features](ARCHERY_ANALYSIS_FEATURES.md)

### For Administrators
1. Follow [Setup Guide](SETUP_GUIDE.md)
2. Review [Project Summary](PROJECT_SUMMARY.md)
3. Understand [System Architecture](ARCHITECTURE.md)

## 📁 Folder Structure

```
docs/
├── INDEX.md (this file)    # Documentation navigation
├── README.md               # Main project README
├── features/               # Feature documentation
│   ├── statistics.md
│   ├── statistics-quick-reference.md
│   ├── statistics-summary.md
│   ├── date-handling.md
│   └── date-fix-summary.md
├── api/                    # API documentation
│   ├── usage-guide.md
│   └── spec.json
├── examples/               # Code examples (future)
└── *.md                    # General documentation

Root docs (general):
├── OVERVIEW.md
├── PROJECT_SUMMARY.md
├── ARCHITECTURE.md
├── SETUP_GUIDE.md
├── FILE_INDEX.md
└── specifications.md
```

## 🚀 Recent Updates

### Statistics Enhancement & Loading States (Latest)
- ✅ Career vs Filtered statistics view
- ✅ Multi-athlete comparison (up to 5)
- ✅ Dynamic auto-refresh on athlete changes
- ✅ **Loading indicators for all API calls**
- ✅ Visual feedback during data fetch
- ✅ Improved UX with loading states

### Date Handling Improvements
- ✅ Multiple date format support
- ✅ Unified timeline for comparisons
- ✅ Proper chronological sorting
- ✅ Italian date display format

## 🔗 External Resources

- **API Endpoint**: https://api.orion-project.it:443
- **FITARCO Results**: https://www.fitarco-italia.org/
- **GitHub Repository**: https://github.com/TheIgorMC

## 📝 Contributing to Documentation

When adding new documentation:
1. Place feature docs in `features/`
2. Place API docs in `api/`
3. Place examples in `examples/`
4. Update this INDEX.md with links
5. Use clear headings and examples
6. Include code snippets where helpful

## ❓ Need Help?

- Check [Quick Start](QUICK_START.txt) for immediate help
- Review [Statistics Quick Reference](features/statistics-quick-reference.md) for usage
- See [Setup Guide](SETUP_GUIDE.md) for installation issues
- Consult [API Usage Guide](api/usage-guide.md) for API problems

## 📄 License & Copyright

Orion Project © 2024-2025
