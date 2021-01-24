import io, requests, json, datetime
import xml.etree.ElementTree as ET
from updateChannels import download_hgo_channel_list, transform_channel_list


def update_epg():
    epg_hgo = download_hgo_epg(days=7)
    epg_filtered = transform_and_filter_hgo_epg(epg_hgo)
    
    channel_list_hgo = download_hgo_channel_list()
    channel_list = transform_channel_list(channel_list_hgo)
    
    epg_xml = transform_epg_to_xmltv_format(epg_filtered, channel_list)
    
    # Write json output to file
    with open("epg.json", "w") as json_output:
        json.dump(epg_filtered, json_output)

    # Write xml output to file
    with io.open("epg.xml", mode="w", encoding="utf-8") as xml_output:
        xml_output.write(ET.tostring(epg_xml, encoding="unicode", method='xml'))

        
    create_m3u8(channel_list)
    

def create_m3u8(channelList):
    with io.open("playlist.m3u8", mode="w", encoding="utf-8") as m3u8_output:
        m3u8_output.write("#EXTM3U\n")
        
        for cID in channelList:
            channel = channelList[cID]
            
            m3u8_output.write("#EXTINF:0 ")
            m3u8_output.write("tvg-id=\"" + channel["id"] + "\" ")
            m3u8_output.write("tvg-chno=\"" + channel["channelno"] + "\" ")
            m3u8_output.write("tvg-name=\"" + channel["name"] + "\" ")
            m3u8_output.write("tvg-logo=\"" + channel["icon"] + "\" ")
            m3u8_output.write("catchup=\"default\" ")
            m3u8_output.write("catchup-source=\"plugin://plugin.video.ziggo/?_=play_video&type=program&channel=" + channel["id"] + "&id={catchup-id}\" ")
            m3u8_output.write("catchup-days=\"7\" group-title=\"TV\" radio=\"false\"," + channel["name"] + "\n")
            m3u8_output.write("plugin://plugin.video.ziggo/?_=play_video&channel=" + channel["id"] + "&id=" + channel["assetid"] + "&\n")
    

def transform_epg_to_xmltv_format(epg, channelList):
    tv = ET.Element("tv")
    
    for cID in channelList:
        channel = channelList[cID]
    
        xmlChannel = ET.SubElement(tv, "channel")
        xmlChannel.set("id", channel["id"])
        
        xmlDisplayName = ET.SubElement(xmlChannel, "display-name")
        xmlDisplayName.text = channel["name"]
        
        xmlIconName = ET.SubElement(xmlChannel, "icon-name")
        xmlIconName.set("src", channel["icon"])
        
        xmlDesc = ET.SubElement(xmlChannel, "desc")
        xmlDesc.text = channel["description"]
        
    
    for cID in epg["channels"]:
        if cID not in channelList:
            continue
    
        epgChannel = epg["channels"][cID]
        for p in epgChannel["programs"]:
            xmlProgramme = ET.SubElement(tv, "programme")
            xmlProgramme.set("channel", epgChannel["id"])
            xmlProgramme.set("start", datetime.datetime.utcfromtimestamp(p["s"]/1000).strftime('%Y%m%d%H%M%S') + " +0000")
            xmlProgramme.set("stop", datetime.datetime.utcfromtimestamp(p["e"]/1000).strftime('%Y%m%d%H%M%S') + " +0000")
            xmlProgramme.set("catchup-id", p["i"])
            
            xmlTitle = ET.SubElement(xmlProgramme, "title")
            xmlTitle.text = p["t"]
            
            xmlDate = ET.SubElement(xmlProgramme, "date")
            xmlDate.text = "2021"
            
            xmlIcon = ET.SubElement(xmlProgramme, "icon")
            xmlIcon.text = ""
            
            xmlDesc = ET.SubElement(xmlProgramme, "desc")
            xmlDesc.text = "Description"
            
            xmlCategory = ET.SubElement(xmlProgramme, "category")
            xmlCategory.text = ""
            
    return tv
    

def download_hgo_epg(date_from=datetime.datetime.now(), days=7):
    result = []

    for day in range(0, days):
        date = (date_from + datetime.timedelta(day)).strftime("%Y%m%d")
        
        print("Request EPG for " + date)
        
        for i in range(1, 5):
            EPG_URL = "https://web-api-pepper.horizon.tv/oesp/v2/HU/hun/web/programschedules/" + date + "/" + str(i)
            
            r = requests.get(EPG_URL, allow_redirects=True)
            
            if not(r.ok):
                raise Exception("EPG cannot be downloaded (" + date + "," + i + ")! Status code: " + str(r.status_code))
            
            epg = r.json()
            
            result.append(epg)
        
    return result
    

def transform_and_filter_hgo_epg(epg):
    result = {
        "startTime": 0000000000,
        "endTime": 0000000000,
        "channels": {}
    }
    
    for i in range(len(epg)):
        epgFragment = epg[i]
    
        # Set startTime
        if (0 == i):
            result["startTime"] = epgFragment["periodStartTime"]
        
        # Set endTime
        if ((len(epg) - 1) == i):
            result["endTime"] = epgFragment["periodEndTime"]
            
        for e in epgFragment["entries"]:
            cID = e["o"]
            if cID not in result["channels"]:
                result["channels"][cID] = {
                    "id": cID,
                    "programs": []
                }
            
            channel = result["channels"][cID]
            programs = channel["programs"]
            
            for p in e["l"]:
                if (len(programs) > 0 and (programs[-1]["s"] == p["s"]) and (programs[-1]["e"] == p["e"])):
                    continue
                
                programs.append(transform_epg_listings_entry(p))

    return result


def transform_epg_listings_entry(le):        
    t = ""
    if "t" in le:
        t = le["t"]
        
    s = 0000000000
    if "s" in le:
        s = le["s"]
        
    e = 0000000000
    if "e" in le:
        e = le["e"]
        
    i = ""
    if "i" in le:
        i = le["i"]
    
    return {
        "t": t,
        "s": s,
        "e": e,
        "i": i
    }

def main():
    print("Update EPG...")
    
    update_epg()
    

if __name__ == "__main__":
    # execute only if run as a script
    main()