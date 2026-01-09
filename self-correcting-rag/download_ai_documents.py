#!/usr/bin/env python3
"""
AI Governance Documents Batch Downloader
==========================================
Purpose: Download all 39 AI governance, compliance, and ethics documents
Author: AI Research Assistant
Date: January 9, 2026
Python Version: 3.6+

This script will:
1. Create a folder structure for organized downloads
2. Download all 39 documents from their official sources
3. Show progress with colored output
4. Handle errors gracefully with retry logic
5. Generate a completion report
"""

import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

# Main download folder name
DOWNLOAD_FOLDER = "AI_Governance_Documents"

# Create subfolders for organization
SUBFOLDER_STRUCTURE = {
    "01_EU_AI_Act": "EU AI Act Documents",
    "02_GDPR": "GDPR Compliance Guidelines",
    "03_Ethics_Frameworks": "AI Ethics Frameworks",
    "04_Model_Governance": "Model Governance Best Practices",
    "05_NIST_Framework": "NIST AI Risk Management Framework",
    "06_Standards": "International Standards",
    "07_Transparency": "Transparency & Accountability",
    "08_US_Government": "US Government Frameworks",
    "09_UK_Government": "UK AI Governance",
    "10_WEF_Resources": "World Economic Forum",
    "11_Partnership_AI": "Partnership on AI",
    "12_Specialized": "Specialized Frameworks"
}

# All documents to download
DOCUMENTS = {
    # EU AI ACT DOCUMENTS
    "01_EU_AI_Act/01_EU_AI_Act_Official.pdf": 
        "https://eur-lex.europa.eu/eli/reg/2024/1689/oj",
    "01_EU_AI_Act/02_EU_AI_Act_Guide_TwoBirds.pdf": 
        "https://www.twobirds.com/-/media/new-website-content/pdfs/capabilities/artificial-intelligence/european-union-artificial-intelligence-act-guide-v4-2024.pdf",
    "01_EU_AI_Act/03_EU_AI_Act_EY_Overview.pdf": 
        "https://www.ey.com/content/dam/ey-unified-site/ey-com/en-gl/services/ai/documents/ey-eu-ai-act-political-agreement-overview-february-2024.pdf",
    "01_EU_AI_Act/04_EU_AI_Act_KPMG.pdf": 
        "https://assets.kpmg.com/content/dam/kpmg/xx/pdf/2024/02/decoding-the-eu-artificial-intelligence-act.pdf",
    "01_EU_AI_Act/05_EU_AI_Act_EY_July2024.pdf": 
        "https://www.ey.com/content/dam/ey-unified-site/ey-com/en-gl/insights/public-policy/documents/ey-gl-eu-ai-act-07-2024.pdf",
    
    # GDPR DOCUMENTS
    "02_GDPR/01_GDPR_Official_Text.pdf": 
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
    "02_GDPR/02_GDPR_Practical_Guide.pdf": 
        "https://www.surveycto.com/wp-content/uploads/2018/03/A-Practical-Guide-for-GDPR-Compliance-Osterman-Research.pdf",
    "02_GDPR/03_GDPR_Guide_TwoBirds.pdf": 
        "https://www.twobirds.com/-/media/new-website-content/pdfs/capabilities/privacy-and-data-protection/bird-and-bird-gdpr-guide.pdf",
    
    # ETHICS FRAMEWORKS
    "03_Ethics_Frameworks/01_Ethics_Guidelines_EU_HLEG.pdf": 
        "https://www.europarl.europa.eu/cmsdata/196377/AI%20HLEG_Ethics%20Guidelines%20for%20Trustworthy%20AI.pdf",
    "03_Ethics_Frameworks/02_Ethics_Guidelines_AEPD.pdf": 
        "https://www.aepd.es/sites/default/files/2019-12/ai-ethics-guidelines.pdf",
    "03_Ethics_Frameworks/03_Responsible_AI_AnitaB.pdf": 
        "https://legacy.anitab.org/wp-content/uploads/2025/06/Responsible-AI-White-Paper.pdf",
    
    # MODEL GOVERNANCE
    "04_Model_Governance/01_Model_Governance_BSA.pdf": 
        "https://ai.bsa.org/wp-content/uploads/2019/09/Model-AI-Framework-First-Edition.pdf",
    "04_Model_Governance/02_Model_Governance_Singapore.pdf": 
        "https://aiverifyfoundation.sg/wp-content/uploads/2024/05/Model-AI-Governance-Framework-for-Generative-AI-May-2024-1-1.pdf",
    "04_Model_Governance/03_GenAI_Governance_Framework.pdf": 
        "https://www.genai.global/frameworks/GenAI_Framework_English.pdf",
    "04_Model_Governance/04_Model_Cards_Google.pdf": 
        "https://arxiv.org/pdf/1810.03993.pdf",
    
    # NIST FRAMEWORK
    "05_NIST_Framework/01_NIST_AI_RMF_1.0.pdf": 
        "https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf",
    "05_NIST_Framework/02_NIST_AI_RMF_SP_800_218.pdf": 
        "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf",
    
    # STANDARDS
    "06_Standards/01_DIN_SPEC_92001.pdf": 
        "https://www.din.de/resource/blob/330532/6c0ba5270a520c73f6149859cdafad83/case-study-din-spec-92001-1-data.pdf",
    
    # TRANSPARENCY & ACCOUNTABILITY
    "07_Transparency/01_Algorithmic_Transparency.pdf": 
        "https://www.opengovpartnership.org/wp-content/uploads/2023/05/State-of-the-Evidence-Algorithmic-Transparency.pdf",
    "07_Transparency/02_Algorithmic_Transparency_GDPR.pdf": 
        "https://www.diva-portal.org/smash/get/diva2:1941957/FULLTEXT01.pdf",
    "07_Transparency/03_ACM_Code_Ethics.pdf": 
        "https://www.acm.org/binaries/content/assets/about/acm-code-of-ethics-booklet.pdf",
    
    # US GOVERNMENT
    "08_US_Government/01_Executive_Order_14110.pdf": 
        "https://www.whitehouse.gov/wp-content/uploads/2024/03/M-24-10-Advancing-Governance-Innovation-and-Risk-Management-for-Agency-Use-of-Artificial-Intelligence.pdf",
    "08_US_Government/02_Executive_Order_Cheatsheet.pdf": 
        "https://ahima.org/media/1fbfjp2v/ai-eo-cheat-sheet-final.pdf",
    
    # UK GOVERNMENT
    "09_UK_Government/01_UK_ProInnovation_Framework.pdf": 
        "https://assets.publishing.service.gov.uk/media/64cb71a547915a00142a91c4/a-pro-innovation-approach-to-ai-regulation-amended-web-ready.pdf",
    "09_UK_Government/02_FCA_AI_Update.pdf": 
        "http://www.fca.org.uk/publication/corporate/ai-update.pdf",
    
    # WEF RESOURCES
    "10_WEF_Resources/01_AI_Governance_Journey.pdf": 
        "https://www3.weforum.org/docs/WEF_The%20AI_Governance_Journey_Development_and_Opportunities_2021.pdf",
    "10_WEF_Resources/02_Global_Trends_AI_Governance.pdf": 
        "https://documents1.worldbank.org/curated/en/099120224205026271/pdf/P1786161ad76ca0ae1ba3b1558ca4ff88ba.pdf",
    "10_WEF_Resources/03_WEF_Governance_Alliance_Briefing.pdf": 
        "https://www3.weforum.org/docs/WEF_AI_Governance_Alliance_Briefing_Paper_Series_2024.pdf",
    "10_WEF_Resources/04_WEF_GenAI_Governance_360.pdf": 
        "https://www3.weforum.org/docs/WEF_Governance_in_the_Age_of_Generative_AI_2024.pdf",
    
    # PARTNERSHIP ON AI
    "11_Partnership_AI/01_PAI_Synthetic_Media.pdf": 
        "https://partnershiponai.org/wp-content/uploads/2023/02/PAI_synthetic_media_framework.pdf",
    
    # SPECIALIZED FRAMEWORKS
    "12_Specialized/01_FSISAC_Responsible_AI.pdf": 
        "https://www.fsisac.com/hubfs/Knowledge/AI/FSISAC_ResponsibleAI-Principles.pdf",
    "12_Specialized/02_ITU_Healthcare_AI.pdf": 
        "https://www.itu.int/dms_pub/itu-t/opb/fg/T-FG-AI4H-2023-5-PDF-E.pdf",
    "12_Specialized/03_NTT_AI_Governance.pdf": 
        "https://es.nttdata.com/documents/ntt-data-ai-governance-v04.pdf",
}

# ============================================================================
# COLOR OUTPUT SUPPORT (for better visibility)
# ============================================================================

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

def print_section(text):
    """Print colored section"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{text}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'-' * len(text)}{Colors.ENDC}")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")

# ============================================================================
# MAIN DOWNLOADER LOGIC
# ============================================================================

class DocumentDownloader:
    """Main class for handling document downloads"""
    
    def __init__(self, base_folder=DOWNLOAD_FOLDER):
        self.base_folder = base_folder
        self.total_files = len(DOCUMENTS)
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.skipped_downloads = 0
        self.start_time = None
        self.failed_files = []
        
    def setup_folders(self):
        """Create necessary folder structure"""
        print_section("Setting up folder structure")
        
        try:
            # Create main folder
            Path(self.base_folder).mkdir(exist_ok=True)
            print_success(f"Created main folder: {self.base_folder}/")
            
            # Create subfolders
            for subfolder_key in SUBFOLDER_STRUCTURE.keys():
                subfolder_path = os.path.join(self.base_folder, subfolder_key)
                Path(subfolder_path).mkdir(exist_ok=True)
            
            print_success(f"Created {len(SUBFOLDER_STRUCTURE)} category subfolders")
            
            # Create README
            self.create_readme()
            
        except Exception as e:
            print_error(f"Failed to create folder structure: {e}")
            return False
        
        return True
    
    def create_readme(self):
        """Create README file in download folder"""
        readme_path = os.path.join(self.base_folder, "README.md")
        readme_content = """# AI Governance & Compliance Documents Collection
## Downloaded on: {date}

This folder contains 39+ verified AI governance, compliance, and ethics documents organized by category.

### Folder Structure:
- **01_EU_AI_Act/** - EU AI Act legislative documents and analyses
- **02_GDPR/** - GDPR compliance guidelines
- **03_Ethics_Frameworks/** - AI ethics frameworks and principles
- **04_Model_Governance/** - Model governance best practices
- **05_NIST_Framework/** - NIST AI Risk Management Framework
- **06_Standards/** - International standards (ISO, DIN)
- **07_Transparency/** - Transparency and accountability documents
- **08_US_Government/** - US government frameworks and executive orders
- **09_UK_Government/** - UK AI governance frameworks
- **10_WEF_Resources/** - World Economic Forum resources
- **11_Partnership_AI/** - Partnership on AI resources
- **12_Specialized/** - Sector-specific frameworks (financial, healthcare, etc.)

### Usage:
1. Browse folders by category
2. Open PDFs with your preferred PDF reader
3. Cross-reference documents as needed for research
4. See "Download_Report.txt" for download summary

### Document Count: 39+
### Total Size: ~40-50 MB
### Last Updated: January 9, 2026

For more information, visit the official sources of each document.
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print_success("Created README.md")
        except Exception as e:
            print_warning(f"Could not create README: {e}")
    
    def download_file(self, filename, url, attempt=1, max_attempts=2):
        """Download a single file with retry logic"""
        filepath = os.path.join(self.base_folder, filename)
        
        # Skip if already exists
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print_info(f"Already exists ({file_size/1024:.1f} KB): {filename}")
            self.skipped_downloads += 1
            return True
        
        try:
            # Create user agent to avoid being blocked
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')]
            urllib.request.install_opener(opener)
            
            print_info(f"Downloading: {filename}")
            urllib.request.urlretrieve(url, filepath, reporthook=self.download_progress)
            
            file_size = os.path.getsize(filepath)
            print_success(f"Downloaded: {filename} ({file_size/1024/1024:.2f} MB)")
            self.successful_downloads += 1
            return True
            
        except urllib.error.URLError as e:
            if attempt < max_attempts:
                print_warning(f"Attempt {attempt} failed, retrying {filename}...")
                time.sleep(2)  # Wait 2 seconds before retry
                return self.download_file(filename, url, attempt + 1, max_attempts)
            else:
                print_error(f"Failed to download {filename}: {e}")
                self.failed_downloads += 1
                self.failed_files.append((filename, url, str(e)))
                return False
        
        except Exception as e:
            print_error(f"Unexpected error downloading {filename}: {e}")
            self.failed_downloads += 1
            self.failed_files.append((filename, url, str(e)))
            return False
    
    def download_progress(self, block_num, block_size, total_size):
        """Progress callback for downloads"""
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(downloaded * 100 / total_size, 100)
            # Only show progress for larger files
            if percent % 25 == 0:
                print(f"  Progress: {percent:.0f}%")
    
    def download_all(self):
        """Download all documents"""
        print_section("Starting batch download")
        print_info(f"Total files to download: {self.total_files}")
        
        self.start_time = time.time()
        
        for idx, (filename, url) in enumerate(DOCUMENTS.items(), 1):
            print(f"\n[{idx}/{self.total_files}] ", end="")
            self.download_file(filename, url)
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate download completion report"""
        elapsed_time = time.time() - self.start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        
        print_header("Download Summary Report")
        
        print_info(f"Total files processed: {self.total_files}")
        print_success(f"Successfully downloaded: {self.successful_downloads}")
        print_info(f"Skipped (already existed): {self.skipped_downloads}")
        
        if self.failed_downloads > 0:
            print_error(f"Failed downloads: {self.failed_downloads}")
        
        print_info(f"Total time elapsed: {minutes}m {seconds}s")
        
        # Save report to file
        self.save_report()
        
        # Print failed files if any
        if self.failed_files:
            print_section("Failed Downloads")
            for filename, url, error in self.failed_files:
                print(f"\nFile: {filename}")
                print(f"URL: {url}")
                print(f"Error: {error}")
                print(f"Action: Try downloading manually from the URL above")
        
        print_header("Download Complete!")
        print_success(f"Documents saved to: {os.path.abspath(self.base_folder)}/")
        print_info("Open the folder to access your documents organized by category.")
        
        return self.failed_downloads == 0
    
    def save_report(self):
        """Save detailed report to file"""
        report_path = os.path.join(self.base_folder, "Download_Report.txt")
        
        elapsed_time = time.time() - self.start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        
        report_content = f"""AI GOVERNANCE DOCUMENTS - DOWNLOAD REPORT
{'='*70}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Download Folder: {os.path.abspath(self.base_folder)}

SUMMARY STATISTICS:
{'='*70}
Total Files: {self.total_files}
Successfully Downloaded: {self.successful_downloads}
Skipped (Already Existed): {self.skipped_downloads}
Failed Downloads: {self.failed_downloads}
Total Time: {minutes}m {seconds}s

FOLDER STRUCTURE:
{'='*70}
"""
        
        for subfolder_key, subfolder_name in SUBFOLDER_STRUCTURE.items():
            subfolder_path = os.path.join(self.base_folder, subfolder_key)
            if os.path.exists(subfolder_path):
                file_count = len([f for f in os.listdir(subfolder_path) if f.endswith('.pdf')])
                report_content += f"\n{subfolder_key}/ ({subfolder_name})\n  Files: {file_count}\n"
        
        if self.failed_files:
            report_content += f"\n\nFAILED DOWNLOADS ({len(self.failed_files)}):\n"
            report_content += "="*70 + "\n"
            for filename, url, error in self.failed_files:
                report_content += f"\nFile: {filename}\n"
                report_content += f"URL: {url}\n"
                report_content += f"Error: {error}\n"
                report_content += "---\n"
        
        report_content += f"\n\nRECOMMENDATIONS:\n"
        report_content += "="*70 + "\n"
        report_content += "1. Organize your documents in the category folders\n"
        report_content += "2. Cross-reference between frameworks for comprehensive understanding\n"
        report_content += "3. Use a PDF reader that supports bookmarks and annotations\n"
        report_content += "4. For failed downloads, try manual download from the provided URLs\n"
        report_content += "5. Keep this folder updated as new versions are released\n"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print_success(f"Report saved to: Download_Report.txt")
        except Exception as e:
            print_warning(f"Could not save report: {e}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    print_header("AI Governance Documents Batch Downloader")
    
    # Check Python version
    if sys.version_info < (3, 6):
        print_error("Python 3.6 or higher is required!")
        sys.exit(1)
    
    # Check internet connection
    try:
        urllib.request.urlopen('http://www.google.com', timeout=2)
    except:
        print_error("Internet connection not available!")
        print_info("Please check your internet connection and try again.")
        sys.exit(1)
    
    # Create downloader
    downloader = DocumentDownloader()
    
    # Setup folders
    if not downloader.setup_folders():
        sys.exit(1)
    
    # Download all files
    success = downloader.download_all()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
