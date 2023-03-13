
visit_domains = ["https://gov.si", "https://evem.gov.si", "https://e-uprava.gov.si", "https://e-prostor.gov.si"]

url = "https://gov.si/testing"

for domain in visit_domains:
    if domain in url:
        print(url)
