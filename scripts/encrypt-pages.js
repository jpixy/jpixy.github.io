#!/usr/bin/env node

/**
 * 页面加密脚本
 * 使用 StatiCrypt 加密指定目录下的 HTML 文件
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// 需要加密的目录（相对于 public/articles/）
const PROTECTED_DIRS = [
  'hft',
  'insights', 
  'interview',
  'leadership',
  'quant'
];

// 从环境变量获取密码
const PASSWORD = process.env.ENCRYPT_PASSWORD;

if (!PASSWORD) {
  console.error('❌ 错误：请设置 ENCRYPT_PASSWORD 环境变量');
  console.error('   本地使用: ENCRYPT_PASSWORD=your_password npm run encrypt');
  console.error('   CI/CD: 在 GitHub Secrets 中设置 ENCRYPT_PASSWORD');
  process.exit(1);
}

const PUBLIC_DIR = path.join(__dirname, '..', 'public', 'articles');

// 密码页面的自定义模板（英文版本）
const TEMPLATE_TITLE = "Password Required";
const TEMPLATE_INSTRUCTIONS = "This content is password protected";
const TEMPLATE_PLACEHOLDER = "Enter password";
const TEMPLATE_BUTTON = "Unlock";
const TEMPLATE_REMEMBER = "7"; // 记住密码天数
const TEMPLATE_REMEMBER_LABEL = "Remember me for 7 days";

/**
 * 递归获取目录下所有 HTML 文件
 */
function getHtmlFiles(dir) {
  const files = [];
  
  if (!fs.existsSync(dir)) {
    console.warn(`⚠️  目录不存在: ${dir}`);
    return files;
  }

  const entries = fs.readdirSync(dir, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...getHtmlFiles(fullPath));
    } else if (entry.name.endsWith('.html')) {
      files.push(fullPath);
    }
  }
  
  return files;
}

/**
 * 加密单个文件
 */
function encryptFile(filePath) {
  const relativePath = path.relative(PUBLIC_DIR, filePath);
  
  try {
    // StatiCrypt 命令
    const cmd = [
      'npx', 'staticrypt',
      `"${filePath}"`,
      '-p', `"${PASSWORD}"`,
      '--remember', TEMPLATE_REMEMBER,
      '--template-title', `"${TEMPLATE_TITLE}"`,
      '--template-instructions', `"${TEMPLATE_INSTRUCTIONS}"`,
      '--template-placeholder', `"${TEMPLATE_PLACEHOLDER}"`,
      '--template-button', `"${TEMPLATE_BUTTON}"`,
      '--template-remember', `"${TEMPLATE_REMEMBER_LABEL}"`,
      '--template-color-primary', '"#2c3e50"',
      '--template-color-secondary', '"#34495e"',
      '-d', `"${path.dirname(filePath)}"`,  // 输出到原目录
      '-f', `"${path.basename(filePath)}"`, // 使用原文件名
      '--short'  // 简短输出
    ].join(' ');
    
    execSync(cmd, { 
      stdio: 'pipe',
      shell: true
    });
    
    console.log(`  ✓ ${relativePath}`);
    return true;
  } catch (error) {
    console.error(`  ✗ ${relativePath}: ${error.message}`);
    return false;
  }
}

/**
 * 主函数
 */
function main() {
  console.log('🔐 开始加密受保护页面...\n');
  
  let totalFiles = 0;
  let encryptedFiles = 0;
  
  for (const dir of PROTECTED_DIRS) {
    const dirPath = path.join(PUBLIC_DIR, dir);
    console.log(`📁 处理目录: articles/${dir}/`);
    
    const htmlFiles = getHtmlFiles(dirPath);
    
    if (htmlFiles.length === 0) {
      console.log('   (无 HTML 文件)\n');
      continue;
    }
    
    for (const file of htmlFiles) {
      totalFiles++;
      if (encryptFile(file)) {
        encryptedFiles++;
      }
    }
    console.log('');
  }
  
  console.log('─'.repeat(40));
  console.log(`✅ 加密完成: ${encryptedFiles}/${totalFiles} 个文件`);
  
  if (encryptedFiles < totalFiles) {
    console.log(`⚠️  ${totalFiles - encryptedFiles} 个文件加密失败`);
    process.exit(1);
  }
}

main();
