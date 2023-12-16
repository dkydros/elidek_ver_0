import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import openpyxl
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
from networkx.algorithms import community

# Cache our data
@st.cache_data()
def load_df():
    #load nodes
    dfn = pd.read_excel("first_test_nodes.xlsx")
    univ_options = dfn.university.unique()
    school_options = dfn.school.unique()
    department_options = dfn.department.unique()
    rank_options = dfn.ranking.unique()

    #load edges
    dfe = pd.read_excel("first_test_edges.xlsx")
    year_options = dfe.Year.unique()
    #min_year = dfe.Year.min()
    #max_year = dfe.Year.max()
    titles = dfe.title
    keywords = dfe.Keywords
    
    return dfn, dfe, univ_options, school_options, department_options, rank_options, year_options, titles, keywords

def check_rows(column, options):
    return res_n.loc[res_n[column].isin(options)]
def check_rows_edges():
    name_search = res_n.name.to_list()
    #print(res_e)
    res_e_new1 = res_e[res_e['source'].isin(name_search)]
    res_e_new2 = res_e[res_e['dest'].isin(name_search)]
    print(res_e_new1, res_e_new2)
    return pd.merge(res_e_new1,res_e_new2)

st.title("Εφαρμογή Δικτυακής Ανάλυσης\n Συνεργασίες Μελών ΔΕΠ Ελληνικών Πανεπιστημίων\nΈκδοση 0.0 (15 Δεκ 23)")

nodes_df, edges_df,  univ_options, school_options, department_options, rank_options, year_options, titles, keywords = load_df()
res_n = nodes_df
res_e = edges_df

#name_query = st.text_input("String match for Name")
tab1, tab2, tab3, tab4 = st.tabs(["Μέλη ΔΕΠ", "Εργασίες", "Δίκτυα", "Στατιστικά"])
with tab1:
    cols = st.columns(4)
    university = cols[0].multiselect("Πανεπιστήμιο", univ_options)
    school = cols[1].multiselect("Σχολή", school_options)
    department = cols[2].multiselect("Τμήμα", department_options)
    ranking = cols[3].multiselect("Βαθμίδα", rank_options)
with tab2:
    cols=st.columns(2)
    years = cols[0].multiselect("Έτη", year_options)
    intitle = st.text_input("Δώσε λέξεις για αναζήτηση στον τίτλο")
    inkeywords = st.text_input("Δώσε λέξεις για αναζήτηση στα keywords")


if university:
    res_n = check_rows("university", university)
    res_e = check_rows_edges() #ενημέρωσε τις ακμές σύμφωνα με τις τρέχουσες κορυφές
if school:
    res_n = check_rows("school", school)
    res_e = check_rows_edges() #ενημέρωσε τις ακμές σύμφωνα με τις τρέχουσες κορυφές
if department:
    res_n = check_rows("department", department)
    res_e = check_rows_edges() #ενημέρωσε τις ακμές σύμφωνα με τις τρέχουσες κορυφές
if ranking:
    res_n = check_rows("ranking", ranking)
    res_e = check_rows_edges() #ενημέρωσε τις ακμές σύμφωνα με τις τρέχουσες κορυφές
if years:
    res_e = res_e.loc[res_e["Year"].isin(years)]
if intitle:
    res_e = res_e.loc[res_e["title"].str.contains(intitle)]
if inkeywords:
    res_e = res_e.loc[res_e["Keywords"].str.contains(inkeywords)]   


with tab1:
    st.write(res_n)
with tab2:
    st.write(res_e)


#now draw
with tab3:
    nodes_df = res_n
    nodes_df.reset_index(inplace = True, drop = True)
    edges_df = res_e
    edges_df.reset_index(inplace = True, drop = True)

    G = nx.from_pandas_edgelist(edges_df, source = 'source', target = 'dest',
                            create_using=nx.MultiDiGraph(),
                            edge_attr = True)
    #here add node attibutes
    nx.set_node_attributes(G, nodes_df.set_index('name').to_dict('index'))

    #here create node titles
    for n in G.nodes(data=True):
        n[1]['title']=n[1]['university']+'\n'+n[1]['school']+'\n'+n[1]['department']+'\n'+n[1]['ranking'] #add hoovering to graph
    #here create edge titles
    for n in G.edges(data=True):
        n[2]['title']=n[2]['title']+'\n'+str(n[2]['DOI'])+'\n'+str(n[2]['Year'])+'\n'+n[2]['Keywords'] #add hoovering to graph
    
    #here create pyvis net
    nt = Network(height='500px', width='500px', directed = True, select_menu=True, filter_menu = True, bgcolor='#FFC0CB', font_color='black', cdn_resources='remote')
    # populates the nodes and edges data structures
    nt.from_nx(G)

    neighbor_map = nt.get_adj_list()
    for node in nt.nodes:
        node["value"] = len(neighbor_map[node["id"]]) #size by degree centrality
    
    colors=['bisque', 'darkorange', 'forestgreen','gold', 'purple', 'olive',
         'limegreen', 'comfortblue', 'lightcoral', 'maroon', 'silver',
         'salmon', 'bisque', 'khaki', 'lime', 'azure', 'violet', 'green', 'black',
         'tomato', 'yellow', 'cyan', 'magenta', 'peru', 'pink', 'turquise']
    color_options = ['community', 'university']
    color_mode_selected = st.selectbox('Επιλέξτε τρόπο χρωματισμού κόμβων',
                                  ('Community', 'university'))
    
    if color_mode_selected =='Community':
        coms = community.greedy_modularity_communities(G)
        if len(coms)>len(colors):
            colors = colors*(len(coms)%len(colors)+1)
    # add neighbor data to node hover data
        for node in nt.nodes:
            for com in coms:
                if node["id"] in com:
                    node["color"] = colors[int(coms.index(com))]
                    break
        nt.show_buttons(filter_=["physics"])
        nt.show('g.html', notebook = False)
    else:
        x = list(univ_options)
        if len(x)>len(colors):
            colors = colors*(len(x)%len(colors)+1)
        for node in nt.nodes:
            node["color"] = colors[int(x.index(node["university"]))]
        nt.show_buttons(filter_=["physics"])
        nt.show('g.html', notebook = False)
    
    nt.save_graph(f'elidek_graph.html')
    HtmlFile = open(f'elidek_graph.html','r',encoding='utf-8')
    
# Load HTML into HTML component for display on Streamlit
    st.header('Δίκτυο Μελών ΔΕΠ')
    
    components.html(HtmlFile.read(), height=800, width=800)
    
    
    with open("elidek_graph.html", "rb") as file:
        btn = st.download_button(
            label="Download Δίκτυο Μελών ΔΕΠ",
            data=file,
            file_name="elidek_graph.html",
            mime="file/html"
        )

#nt.show('g.html', notebook = False)


