### Date Check Selectors ###
date_content_selector = "div[data-sigil='m-feed-voice-subtitle']  > a > abbr"
location_content_selector = "div[data-sigil='m-feed-voice-subtitle'] > a:nth-of-type(2)"
post_link_selector = "div[data-sigil='m-feed-voice-subtitle']  > a"

### Post Contents Selectors ###
post_header_selector = "h2[id*='jsc']"
page_post_content_selector = "div[data-ad-comet-preview='message']"
group_post_content_selector = "div.rq0escxv.a8c37x1j.rz4wbd8a.a8nywdso > div:nth-of-type(2),div[data-ad-comet-preview='message']"
page_author_name_xpath_selector = "//*[contains(@id,'jsc_c')]/div/a/strong/span"
profile_author_name_selector = "div._7om2._52wc>div>h3>span>strong"
profile_author_name_other_text_selector = "div._7om2._52wc>div>h3>strong"
profile_checkin_mentions_selector = "h2.gmql0nx0.l94mrbxd.p1ri9a11.lzcic4wl.aahdfvyu.hzawbc8m"

### Post like count, share_count and comment count selectors ###
share_count_selector_1 = "div.bp9cbjyn.j83agx80.pfnyh3mw.p1ueia1e > div:nth-of-type(1)"
share_count_selector_2 = "div.bp9cbjyn.j83agx80.pfnyh3mw.p1ueia1e > div:nth-of-type(2)"

like_count_selector = "div[data-sigil='reactions-sentence-container'] > div"
cmt_count_selector = "div.bp9cbjyn.j83agx80.pfnyh3mw.p1ueia1e > div:nth-of-type(1)"

### Image Content Selectors ###
image_holder_selector  = "div._5rgu._7dc9._27x0 > div > div > a:nth-of-type(1)"
image_paginator_selector = "div.rq0escxv.l9j0dhe7.du4w35lb > div > div > div > div.rq0escxv.l9j0dhe7.du4w35lb > div > div.j83agx80.cbu4d94t.h3gjbzrl.l9j0dhe7.du4w35lb.qsy8amke > div.nznu9b0o.ji94ytn4.q10oee1b.r893ighp.ni8dbmo4.stjgntxs.k4urcfbm.spskuzq3.a156tdzh > div > div.cwj9ozl2.j83agx80.cbu4d94t.datstx6m.owwhemhu.ni8dbmo4.stjgntxs.spskuzq3 > div > div.tqsryivl.j83agx80.cbu4d94t.buofh1pr.ni8dbmo4.stjgntxs.l9j0dhe7.r9f5tntg.j9dqwuog > div.bp9cbjyn.tqsryivl.j83agx80.cbu4d94t.buofh1pr.datstx6m.taijpn5t.ni8dbmo4.stjgntxs.l9j0dhe7.abiwlrkh.k4urcfbm > div.du4w35lb.giggcyz0 > div"


page_image_selector = "i[data-sigil='photo-image']"
page_next_btn_selector = "a._57-r.touchable"

gp_image_selector = "div.du4w35lb.k4urcfbm.stjgntxs.ni8dbmo4.taijpn5t.buofh1pr.j83agx80.bp9cbjyn"
gp_next_btn_selector = "div[aria-label='View next image']"

# video_btn_selector = "div.i09qtzwb.rq0escxv.n7fi1qx3.pmk7jnqg.j9ispegn.kr520xx4.nhd2j8a9 > div > div"
# video_btn_selector = "div.k4urcfbm.kr520xx4.pmk7jnqg.datstx6m > i > div > img"
page_video_btn_selector = "div.bp9cbjyn.j83agx80.buofh1pr.taijpn5t.k4urcfbm.datstx6m"
gp_video_btn_selector = "div.i09qtzwb.rq0escxv.n7fi1qx3.pmk7jnqg.j9ispegn.kr520xx4.nhd2j8a9"

# Profile Extractor
profile_image_selector = "//div[@aria-label='Profile picture actions']"
profile_post_content_up_selector = "div[class='_5rgt _5nk5 _5wnf _5msi']"
profile_post_content_up_1_selector = "div[class='_5rgt _5nk5 _5msi']"
profile_post_content_up_2_selector = "div[class='_5rgt _5nk5']"
profile_post_content_down_selector = "div[class='_5rgu _7dc9 _27x0']"
profile_post_content_with_background_selector = ".//span[@class='_2z79']"
profile_post_content_with_link_selector = ".//div[@class='ecm0bbzt hv4rvrfc ihqw7lf3 dati1w0a']/div/div/span"
# profile_post_content_with_blockquote_selector = ".//blockquote[@class='h2mp5456 mk2mc5f4 peup4ujy cxmmr5t8 dhix69tm sej5wr8e aahdfvyu hv4rvrfc dati1w0a']/span/div"
profile_post_content_with_blockquote_selector = "blockquote.dati1w0a > span > div"
profile_post_content_with_bold_font_selector = ".//div[@class='qt6c0cv9 hv4rvrfc dati1w0a jb3vyjys']"
profile_post_content_bio_selector = ".//div[@class='dati1w0a ihqw7lf3 hv4rvrfc discj3wi']"
profile_post_content_jobs_location_selector = ".//div[@class='rq0escxv a8c37x1j rz4wbd8a a8nywdso']"
profile_post_content_avatar_selector = ".//img[@data-imgperflogname='feedCoverPhoto']"
profile_user_id_link_selector = "//h2[@class='gmql0nx0 l94mrbxd p1ri9a11 lzcic4wl aahdfvyu hzawbc8m']/strong/span/a"
articles_selector = "//article"
intro_selector = "//div[@data-pagelet='ProfileTilesFeed_0']"
intro_text_class_selector = "//div[@class='rq0escxv l9j0dhe7 du4w35lb j83agx80 cbu4d94t g5gj957u d2edcug0 hpfvmrgz rj1gh0hx buofh1pr o8rfisnq p8fzw8mz pcp91wgn iuny7tx3 ipjc6fyt']"
profile_click_see_more_selector = "span[data-sigil='more'] > a"
profile_click_see_more_default_selector = "div[data-ad-preview='message'] > div > div > span > div:last-of-type > div > div"
profile_click_others_selector = "//div[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'others') and @role='button']"

