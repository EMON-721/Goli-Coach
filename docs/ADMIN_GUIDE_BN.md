# অ্যাডমিন চালু করা

অনলাইন static সংস্করণে অ্যাকাউন্ট সার্ভার যুক্ত নেই। পূর্ণ সোর্সে Python server আছে। README অনুযায়ী একই origin-এ সার্ভার চালান। প্রথমে নিজের অ্যাকাউন্ট register করুন। সার্ভার console-এ `.venv/bin/python server/bootstrap_admin.py` চালিয়ে সেই ইমেইল দিন। নতুন করে login করুন। কোনো default admin password নেই।

`/admin/`: JSON-এ brand, hero_bn/en, about_bn/en, cta_bn/en এডিট → Save draft → Publish saved draft। আগের সংস্করণ থাকলে Rollback। প্রকাশিত কন্টেন্ট পুনরায় public UI খুললে দেখা যাবে।

Sources: URL ও লাইসেন্সের প্রমাণ দিয়ে quarantine-এ যোগ করুন। এটি importer নয়; কোনো ডেটা স্বয়ংক্রিয়ভাবে প্রকাশিত/প্রশিক্ষণে ব্যবহার হয় না। Models: প্রকৃত server health দেখুন, server model disable/enable করুন। এই switch browser-local model বন্ধ করে না। Users: metadata-only directory; audit ও feedback role অনুযায়ী দেখা যাবে। Private clips/reports অন্যের জন্য বন্ধ, superadmin-ও দেখতে পারবেন না।

পূর্ণ V5 CMS নয়: সব টেক্সট/লোগো/রঙ/পেজ বিন্যাস, scheduled publishing, coach verification, imports/approvals, backup UI, MFA ও notifications এখনো অসম্পূর্ণ। বর্তমান UI-কে পূর্ণ production admin বলবেন না।

## ২৯ অক্টোবরের সংযোজন
CMS-এ লেখা, FAQ, ড্রিল ও নেভিগেশন ফর্মে সম্পাদনা করুন। Save draft-এর পর Publish this draft চাপুন। ইতিহাস থেকে নির্দিষ্ট সংস্করণ ফেরানো যায়। Users-এ role/blocking, Feedback-এ status, Sources-এ rights evidence ও review state বদলানো যায়। সব পরিবর্তনে server-side role পরীক্ষা থাকে।
