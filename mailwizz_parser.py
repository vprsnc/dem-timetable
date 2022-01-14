import mechanize
import http.cookiejar as cookielib
import bs4 as bs


def scrape_from_mailwizz():
    # Browser
    br = mechanize.Browser()

    # Cookie Jar
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)

    # Browser options
    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    br.addheaders = [('User-agent', 'Chrome')]

    # The site we will navigate into, handling it's session
    br.open('http://affariinrussia.com/news/customer/index.php/guest/index')

    # View available forms
    # for f in br.forms():
    #     print(f)
    #     print(f._pairs())

    # Select the second (index one) form (the first form is a search query box)
    br.select_form(nr=1)

    # User credentials
    br.form['CustomerLogin[email]'] = 'g.toporkov@eunioncapital.com'
    br.form['CustomerLogin[password]'] = 'Br#N2CukscN@WEBh0g'

    # Login
    br.submit()

    page = br.open(
        'http://affariinrussia.com/news/customer/index.php/campaigns/index/page/1?ajax=Campaign-grid&page_size=100'
        ).read()
    soup = bs.BeautifulSoup(page, 'lxml')
    body = soup.find('div', id='Campaign-grid', class_='grid-view')
    tbody = body.find('tbody')
    rows = tbody.find_all('tr')

    data = []
    for row in rows:
        campaign = row.find_next('td').find_next('td').find_next('td').find_next(
            'td').text
        planned = row.find_next('td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next('td').find_next('td'
                                                                            ).find_next('td').find_next('td').text
        sent = row.find_next('td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next('td').text
        opens = row.find_next('td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next('td').find_next(
            'td').find_next('td').text
        clicks = row.find_next('td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').text
        bounces = row.find_next('td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next('td').text
        unsubs = row.find_next('td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next('td').find_next(
            'td').find_next('td').find_next('td').find_next(
            'td').find_next('td').text
        scraped_data = {
            'Campaign': campaign,
            'Planned': planned,
            'Sent': sent,
            'Opens': opens,
            'Clicks': clicks,
            'Bounces': bounces,
            'Unsubs': unsubs,
        }

        data.append(scraped_data)

    return data
