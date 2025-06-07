# 🚀 GitHub Repository Setup Guide

## Quick Setup Steps

### 1. Create Repository on GitHub

1. **Go to GitHub**: Visit [github.com/MarcBaumholz](https://github.com/MarcBaumholz)
2. **Create New Repository**:
   - Click the green "New" button
   - Repository name: `discord-bots-collection`
   - Description: `🤖 Collection of 8 specialized Discord bots for productivity, planning, and automation with Docker containerization`
   - Make it **Public**
   - **DO NOT** initialize with README, .gitignore, or license (we have our own)
   - Click "Create repository"

### 2. Create Personal Access Token (if needed)

If your current token doesn't work, create a new one:

1. **Go to Settings**: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. **Generate new token**:
   - Note: `Discord Bots Repository Access`
   - Expiration: `90 days` or as needed
   - **Select scopes**:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `workflow` (Update GitHub Action workflows)
   - Click "Generate token"
   - **COPY THE TOKEN** - you won't see it again!

### 3. Push Your Code

**Option A: Use the automated script**
```bash
./push_to_github.sh
```

**Option B: Manual push**
```bash
# Remove current remote
git remote remove origin

# Add your new repository (replace with your actual token)
git remote add origin https://MarcBaumholz:YOUR_NEW_TOKEN@github.com/MarcBaumholz/discord-bots-collection.git

# Push to GitHub
git push -u origin main
```

## 🎯 Repository Configuration (After Push)

### Add Repository Details
1. **Description**: `🤖 Collection of 8 specialized Discord bots for productivity, planning, and automation with Docker containerization`
2. **Website**: `https://marcbaumholz.de` (optional)
3. **Topics**: Add these tags:
   - `discord-bot`
   - `python`
   - `docker`
   - `automation`
   - `productivity`
   - `notion-api`
   - `raspberry-pi`
   - `containerization`

### Create a License (Recommended)
1. Go to your repository
2. Click "Add file" → "Create new file"
3. Name: `LICENSE`
4. Use the template button to add MIT License
5. Commit the file

### Repository Settings (Optional)
- **Discussions**: Enable for community feedback
- **Issues**: Already enabled by default
- **Projects**: Consider creating a project board for development
- **Security**: Review security settings

## 🔒 Security Notes

- ✅ `.env` file is properly excluded via `.gitignore`
- ✅ All example files use placeholder values
- ✅ No hardcoded secrets in the code
- ⚠️ **Never commit your actual `.env` file**
- 🔄 Rotate your Discord bot token if it was ever committed

## 📋 After Setup Checklist

- [ ] Repository created and code pushed
- [ ] Description and topics added
- [ ] LICENSE file added
- [ ] .env.example file verified (no real secrets)
- [ ] Docker setup tested locally
- [ ] README.md displays correctly
- [ ] Repository starred ⭐

## 🆘 Troubleshooting

### Push Denied Error
- **Check token scopes**: Must include `repo`
- **Verify repository exists**: Make sure you created it on GitHub
- **Try HTTPS instead of SSH**: Use token authentication

### Secret Detection Error
- **Check all .example files**: Ensure they have placeholder values only
- **Verify .gitignore**: Should exclude `.env` files
- **Clear git history**: If secrets were committed, may need to rewrite history

### 403 Permission Error
- **Generate new token**: With proper `repo` scope
- **Check repository ownership**: Make sure you own the repository
- **Verify username**: Double-check username in the URL

---

🎉 **Once setup is complete, your Discord bots will be publicly available and ready for collaboration!** 