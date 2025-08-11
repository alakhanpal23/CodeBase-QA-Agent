#!/usr/bin/env python3
"""
Frontend End-to-End Tests using Selenium
Tests the complete user journey through the web interface
"""

import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

FRONTEND_URL = "http://localhost:3001"

class FrontendTestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"✅ {test_name}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ {test_name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"FRONTEND TEST SUMMARY: {self.passed}/{total} tests passed")
        if self.failed > 0:
            print(f"❌ {self.failed} tests failed:")
            for error in self.errors:
                print(f"   - {error}")
        print(f"{'='*60}")
        return self.failed == 0

def setup_driver():
    """Setup Chrome WebDriver with appropriate options"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        return driver
    except Exception as e:
        print(f"❌ Failed to setup WebDriver: {e}")
        print("💡 Make sure Chrome and ChromeDriver are installed")
        return None

def test_homepage_load(driver, results):
    """Test homepage loading and basic elements"""
    try:
        driver.get(FRONTEND_URL)
        
        # Check if page title contains expected text
        WebDriverWait(driver, 10).until(
            lambda d: "CodeBase QA" in d.title or len(d.title) > 0
        )
        
        # Check for main heading
        heading = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        if "CodeBase QA" in heading.text or "Ask Questions" in heading.text:
            results.add_pass("Homepage Load")
        else:
            results.add_fail("Homepage Load", "Main heading not found or incorrect")
            
    except TimeoutException:
        results.add_fail("Homepage Load", "Page load timeout")
    except Exception as e:
        results.add_fail("Homepage Load", str(e))

def test_navigation_links(driver, results):
    """Test navigation between pages"""
    try:
        driver.get(FRONTEND_URL)
        
        # Test navigation to repositories page
        repos_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Repositories"))
        )
        repos_link.click()
        
        # Wait for repositories page to load
        WebDriverWait(driver, 10).until(
            lambda d: "/repos" in d.current_url
        )
        
        # Check for repositories page content
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TEXT, "Repository Management"))
        )
        
        results.add_pass("Navigation to Repositories")
        
        # Test navigation to chat page
        driver.get(FRONTEND_URL)
        chat_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Chat"))
        )
        chat_link.click()
        
        WebDriverWait(driver, 10).until(
            lambda d: "/chat" in d.current_url
        )
        
        results.add_pass("Navigation to Chat")
        
    except TimeoutException:
        results.add_fail("Navigation Links", "Navigation timeout")
    except Exception as e:
        results.add_fail("Navigation Links", str(e))

def test_repository_form(driver, results):
    """Test repository addition form"""
    try:
        driver.get(f"{FRONTEND_URL}/repos")
        
        # Find the repository URL input
        url_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='url']"))
        )
        
        # Test form validation with invalid URL
        url_input.clear()
        url_input.send_keys("invalid-url")
        
        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Browser should show validation error
        if url_input.get_attribute("validity").get("valid") == False:
            results.add_pass("Repository Form Validation")
        else:
            results.add_fail("Repository Form Validation", "Invalid URL not caught")
        
        # Test with valid URL (but don't actually submit to avoid long wait)
        url_input.clear()
        url_input.send_keys("https://github.com/test/repo")
        
        if url_input.get_attribute("validity").get("valid") != False:
            results.add_pass("Repository Form Valid Input")
        else:
            results.add_fail("Repository Form Valid Input", "Valid URL rejected")
            
    except TimeoutException:
        results.add_fail("Repository Form", "Form elements not found")
    except Exception as e:
        results.add_fail("Repository Form", str(e))

def test_chat_interface(driver, results):
    """Test chat interface elements"""
    try:
        driver.get(f"{FRONTEND_URL}/chat")
        
        # Check for chat input
        chat_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='question']"))
        )
        
        # Check for send button
        send_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        # Test that input is initially disabled (no repos selected)
        if chat_input.get_attribute("disabled"):
            results.add_pass("Chat Input Disabled (No Repos)")
        else:
            results.add_fail("Chat Input Disabled (No Repos)", "Input should be disabled when no repos selected")
        
        # Check for repository selector
        try:
            repo_selector = driver.find_element(By.TEXT, "Repositories")
            results.add_pass("Chat Repository Selector")
        except NoSuchElementException:
            results.add_fail("Chat Repository Selector", "Repository selector not found")
        
        # Check for welcome message
        try:
            welcome_text = driver.find_element(By.TEXT, "Welcome")
            results.add_pass("Chat Welcome Message")
        except NoSuchElementException:
            results.add_fail("Chat Welcome Message", "Welcome message not found")
            
    except TimeoutException:
        results.add_fail("Chat Interface", "Chat elements not found")
    except Exception as e:
        results.add_fail("Chat Interface", str(e))

def test_responsive_design(driver, results):
    """Test responsive design at different screen sizes"""
    screen_sizes = [
        (1920, 1080, "Desktop"),
        (768, 1024, "Tablet"),
        (375, 667, "Mobile")
    ]
    
    for width, height, device in screen_sizes:
        try:
            driver.set_window_size(width, height)
            driver.get(FRONTEND_URL)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            
            # Check if main content is visible
            main_content = driver.find_element(By.TAG_NAME, "main")
            if main_content.is_displayed():
                results.add_pass(f"Responsive Design - {device}")
            else:
                results.add_fail(f"Responsive Design - {device}", "Main content not visible")
                
        except Exception as e:
            results.add_fail(f"Responsive Design - {device}", str(e))

def test_accessibility_basics(driver, results):
    """Test basic accessibility features"""
    try:
        driver.get(FRONTEND_URL)
        
        # Check for alt text on images
        images = driver.find_elements(By.TAG_NAME, "img")
        images_with_alt = [img for img in images if img.get_attribute("alt")]
        
        if len(images) == 0 or len(images_with_alt) == len(images):
            results.add_pass("Image Alt Text")
        else:
            results.add_fail("Image Alt Text", f"{len(images) - len(images_with_alt)} images missing alt text")
        
        # Check for proper heading hierarchy
        headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
        if len(headings) > 0:
            results.add_pass("Heading Structure")
        else:
            results.add_fail("Heading Structure", "No headings found")
        
        # Check for form labels
        inputs = driver.find_elements(By.TAG_NAME, "input")
        labeled_inputs = []
        for input_elem in inputs:
            input_id = input_elem.get_attribute("id")
            if input_id:
                try:
                    driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                    labeled_inputs.append(input_elem)
                except NoSuchElementException:
                    pass
            # Also check for aria-label or placeholder
            if (input_elem.get_attribute("aria-label") or 
                input_elem.get_attribute("placeholder")):
                labeled_inputs.append(input_elem)
        
        if len(inputs) == 0 or len(labeled_inputs) >= len(inputs) * 0.8:  # 80% threshold
            results.add_pass("Form Labels")
        else:
            results.add_fail("Form Labels", "Some form inputs lack proper labels")
            
    except Exception as e:
        results.add_fail("Accessibility Basics", str(e))

def test_error_states(driver, results):
    """Test error state handling in UI"""
    try:
        # Test with backend potentially down
        driver.get(f"{FRONTEND_URL}/repos")
        
        # Wait for page to load
        time.sleep(3)
        
        # Look for error messages or loading states
        error_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='error'], [class*='Error']")
        loading_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='loading'], [class*='Loading']")
        
        # The page should handle errors gracefully
        if len(error_elements) > 0 or len(loading_elements) > 0:
            results.add_pass("Error State Handling")
        else:
            # If no explicit error/loading states, check if page still functions
            try:
                driver.find_element(By.CSS_SELECTOR, "input[type='url']")
                results.add_pass("Error State Handling (Graceful Degradation)")
            except NoSuchElementException:
                results.add_fail("Error State Handling", "Page broken when backend unavailable")
                
    except Exception as e:
        results.add_fail("Error State Handling", str(e))

def main():
    """Run all frontend tests"""
    print("🌐 Starting Frontend End-to-End Tests")
    print("=" * 60)
    
    results = FrontendTestResults()
    
    # Setup WebDriver
    driver = setup_driver()
    if not driver:
        print("❌ Cannot run frontend tests without WebDriver")
        return 1
    
    try:
        # Basic functionality tests
        print("\n🏠 HOMEPAGE TESTS")
        test_homepage_load(driver, results)
        
        print("\n🧭 NAVIGATION TESTS")
        test_navigation_links(driver, results)
        
        print("\n📝 FORM TESTS")
        test_repository_form(driver, results)
        
        print("\n💬 CHAT INTERFACE TESTS")
        test_chat_interface(driver, results)
        
        print("\n📱 RESPONSIVE DESIGN TESTS")
        test_responsive_design(driver, results)
        
        print("\n♿ ACCESSIBILITY TESTS")
        test_accessibility_basics(driver, results)
        
        print("\n🚨 ERROR HANDLING TESTS")
        test_error_states(driver, results)
        
    finally:
        driver.quit()
    
    # Final summary
    success = results.summary()
    
    if success:
        print("\n🎉 ALL FRONTEND TESTS PASSED!")
        return 0
    else:
        print("\n⚠️  Some frontend tests failed.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)