import type {
  AnimeSummary,
  CollectionItem,
  CollectionStatus,
  FavoriteRankItem,
  ListResponse,
  UserProfile,
  UserSettings,
} from '../types'

const nowIso = new Date().toISOString()

export const mockCurrentUser: UserProfile = {
  id: 1,
  username: 'collector_a',
  public_slug: 'collector_a',
  display_name: 'Collector A',
  avatar_url:
    'https://lh3.googleusercontent.com/aida-public/AB6AXuDthqI7XD4ONHe9geKPQgya_xoIgZCXmXyxuvN0Y-zF0vZ97AB9C3OLZkHm9Yyo4aMltAUJI-zjZNy3akpB5n54rRDAolSqnHH6OxLxZwD212ORuZBIY83aUpQ0PrwCnLmPDewSdqGwJi0mAlLq7jwiv50vpdm4Z9BT4X2br4tHztRV8uQo9C6sFAULyufjV2zM6_2HLZvNRL5-Kab5SgQqAmj7qXHPodkz1SrFJg7-oUSwbTUFCvdLv21bITeDr9GoWgwQEhLsSCc',
  background_image_url: null,
  birthday: '2000-05-24',
  bio: 'Weaving fragments of anime memories.',
  is_public: true,
}

export const mockPublicUser: UserProfile = {
  id: 2,
  username: 'hoshino',
  public_slug: 'hoshino',
  display_name: 'Hoshino',
  avatar_url:
    'https://lh3.googleusercontent.com/aida-public/AB6AXuBz2g3buqSNw3sbE3ecB-1ubetIRYPX9la0BjAH9e-2HKgTepI42_5XI5ChScI4KJK9Vo-O9acS7cF4cdrhj396rr8tdJNgVxj4o_pkSPdw4jtGsXatX0nzKDXTxZ9Aet2a8rOqZZKLTwPAozpbVPTpYKzD4cW7iWoFhM8id-OFXi2SOTaO9r4JN9nLRaBpcq9qF-HZbJvElZR0dqhSTjZVYZdtmLziszufrSpdXnSsAlgjuiEEZU5BTUy96ynRHTJf5GKGOCg6rMo',
  background_image_url: null,
  birthday: null,
  bio: 'A shelf for timeless scenes and stories.',
  is_public: true,
}

export const mockUserSettings: UserSettings = {
  language: 'zh-CN',
  show_dynamic_background: true,
  show_public_rank: true,
}

export const mockAnimePool: AnimeSummary[] = [
  {
    id: 101,
    title: 'Frieren: Beyond Journey End',
    summary: 'A gentle and profound road after the ending.',
    year: 2024,
    season: 'SPRING',
    genres: ['Fantasy', 'Healing'],
    cover_url:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuDULR9cKJWRrWYtMvCjwv5nSTyd2eRXuSyfdhNwtVLaC66e1zqAWgk1xrq96Tq76MF8trl5IPKt0gFgNrBfAqN6oyBjP4RfycHQt45fAhlSXYag-mf9each2eN47jT4oaqDdxMjj-5N-hsaffHw1EOxLg96xYUF_bZaoaoqnnannOaL6s_M4Dr_ER-rlNKxyGhOjGvHoi8QzIv0-nJnM9-l3Mcr9GzxJ1B_3dprgAum-d6wpNcVCLQq7hQeX8A1J5vdNqLQf89jd1w',
  },
  {
    id: 102,
    title: 'Cyberpunk: Edgerunners',
    summary: 'A red romance in a neon city.',
    year: 2023,
    season: null,
    genres: ['Action', 'Sci-Fi'],
    cover_url:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuD3QZSn-D5g2lbfe9YyhnL-bJUFvJdKZyQO1kPJlu1E9kYbXr0LQ3Sk5UAf3a-PjN4Q8PtNK2c0UfFsC8EjpjPJgDJsbgP1Ag8U_0-J3qv_MjYFfijQYym5lVeaOeCJNvdtTilS6N7LLGxPMaT8iKYS6_fGY-bnWDesbwbeWYUCz7eyTd1Eff9_GCcF2EO9C3RWctivpEJlpiia-nmX4ApBhCmaurEQA10R0shNnc26mwBsuyq6Xi2gyghCxRfrFpo4NNDIDTbasnc',
  },
  {
    id: 103,
    title: 'Natsume Book of Friends',
    summary: 'Soft bonds between human and spirit.',
    year: 2016,
    season: null,
    genres: ['Healing', 'Fantasy'],
    cover_url:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuBrDldeEXILv-x2jIJQipYLuttLv_MTsQLitBYSfo1m6EmKOqEA2Rl6LSMv_WnpAlguO_vEbV9MEZkERbQAqofhPbazjJ64Jg8p9nR409zDtN0yZRrXCEgeJAj3YZsxDRGfVy3Z-lu_rmp3DGRaAlOlv-69_94RpDOdZukgKinCms6spXzhTi1PJujLHNI7N4ho9e1FuVwrSv_4L3qAoT6YcOeRhQrKACnD2JCaTUoMsK6XQ7svLvvCjEZTl7werePI6rkxazpxxk0',
  },
  {
    id: 104,
    title: 'Neon Genesis Evangelion',
    summary: 'The final narrative of solitude and growth.',
    year: 1995,
    season: null,
    genres: ['Psychological', 'Mecha'],
    cover_url:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuDhWh6nQmTawtC_Nw1J_5Z3sGZO8xL7uEjM_nTbWb4-kBoWjMKVIsBjNYBW7ZeSPCqzQ9GWsOp8m_q05kCa0q4F7gBhj83EoEda7JYONbZzRN87ByfjMN_n85wXbRyGLBX4IwtME4zl5jHLxbm-J-ddbJVNvytN0l4RzdQ3zoHWLHK5owjCszt5WZdPBAK9nCsnsIb_IZnurw6d7iQrylAAEF2fQ0edqL_eRKNcRO0BH_lB07DMez7QFdoj-0knCfmB7V9tszMVxcg',
  },
  {
    id: 105,
    title: 'Your Name',
    summary: 'Two lives crossing through time and memory.',
    year: 2016,
    season: null,
    genres: ['Romance', 'Fantasy'],
    cover_url:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuC_hryU0Y17ZRUdjzga7axKDdCZPUquX7A1m1fd4ubNaPVTWc1v8Um7WxjT2xo4zm0QMaCvGXPYtVV7ng0xX4R8WQVe2CtUKj8uiLTiniyn8Slf3A95nqDmW-s80PKkD7La00-5N74Uq-aNTUBSMA3YE_iF0VOL1Z0f6VLAze8QVsJlpxlloHnCRE_yp1FOMFn42AIp_AExBLVWrycQOozZ_-ZNp5_l2HTd4M_7r5kyfHbWvCV5YBsNjaWAB4aFIc4a5_4C2ocvJms',
  },
  {
    id: 106,
    title: 'Demon Slayer: Hashira Training',
    summary: 'Blades and bonds rush toward the final arc.',
    year: 2024,
    season: 'SPRING',
    genres: ['Action', 'Shonen'],
    cover_url:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuDUpKgrRiVOCRJihFDbg5I0TXXJhGC0EJNWG2lVv746AfI-jiBNTxD88zunBTtDToxUXcDkK-F6IR2afVt3CXo_PM83W_YuKAvt-3fXhlYeidI_4yTsFmjeCRxA4MccFPm4DCXuuotf-n2XqMd9SA8mitF8Xcy2-0bpdqESesC_YW9BV7DtQbQzXBH4ClEzu_j6koY1SjlIwHtEUJJrOvjAc2EL8USqyaHV2K4OfigEhF_QKfxC-_dOAMPdTNLhkS2iEBbCoASmXYk',
  },
  {
    id: 107,
    title: 'Delicious in Dungeon',
    summary: 'Adventure and cooking in the labyrinth.',
    year: 2024,
    season: 'WINTER',
    genres: ['Adventure', 'Comedy'],
    cover_url:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuChCo8YTdmvMKs9ewMyOShzzXqqXGZQ2BbLxQ1ZYhTi-8nEYycLW3N4mnxnnZNI7lUzSejv7idbfXQg1B8yfj2NSxhROZ2mKjUJuFxNtIqxL4rPa062RC7a_VpUDsJlJYfZQQ1BkzLPqV4thvrLv90BnTrBROR4XEgSwjEK6A8atHdL-bddyjajf5JqFQ0yPK9oOCHl1-k1O6Etw4jwm3hEi7peoWjB4BRfiIoLLhXiIVJV2Ez_F5TQCVuVOCFyi3YZEQN_7veI678',
  },
  {
    id: 108,
    title: 'Haikyu!!',
    summary: 'Continuous growth on the volleyball court.',
    year: 2023,
    season: null,
    genres: ['Sports', 'Shonen'],
    cover_url:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuB5R2yCXb25rOhnHSylsXi-L1CykO2RtmFX3hvRZA3EM2LCKY612AnPClI2ZQaH25YxruI_9oAZ5rePa0CTWyTzNepNW_H4T5fIlr3Uq0Qgd2h_SezXcEnZd5I-xLuf_gBGDO7Hyav3py5mXdkIFqWVx9qiNo0dwHZxaaNB8Di-EoQhmsMBdUUC5AHvmA95GvJdH0h39K9M7sn38VFkoXQ3U72Y-HZkoYqynFXxcROf2kXR9R_FY3RjWQvZuDr8pfkTvCqyfH9XDx0',
  },
  {
    id: 109,
    title: 'Jujutsu Kaisen 0',
    summary: 'A theater story of curse and salvation.',
    year: 2022,
    season: null,
    genres: ['Action', 'Fantasy'],
    cover_url:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuDMOaAWsT2wd2-8Kye3sU1kVFtumtHH-7rV6K4FOsboUJhJG1nxy3NzknAXWyOprgRJCeFTYgp8n_jnj-grKXL6iG-cLDJfUER70jPe684mkoMkZeK7VmoGlSPfqAI-hecUWaGimyiPaZGjCJzKkR08azZJ9AwVM5D8LGviEB8CdDY2UR9wk2wb7fb4a4WA9RbBbja6zwJxWj2t4xqL4ehFHGeQeVuTuGt8j6A0loH9WmaGKmknvxJMdH-na7wPP14yvL1h_V4rLKg',
  },
  {
    id: 110,
    title: 'Puella Magi Madoka Magica',
    summary: 'A dark truth beneath a cute shell.',
    year: 2011,
    season: null,
    genres: ['Magic', 'Dark'],
    cover_url:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuAm2McecrwbkmbC7zb5aJYqnHmbBxiHAJi9o819Oj-AYxnow4yW9eMH7kQHWu2dVw4prhRdrHC6nx6qrM_9fXOE_dBr-K1YwRUSW9YK-Ov5qmTbADJBBfeb5l6Sgs22aMpo3r8Yo6Y1Wj5hE07z4PL8I8iXi_y6b2rjlWAlaU0A7j2FxFh3huLDbNmt3LcJztncPUsE8AQ_fJWSluXtEMXuKm4s2kOyViTM9qX_eQAuxPHVS01EiLqUgMVyBFPeJqyr1YTyDlWNZ-g',
  },
  {
    id: 111,
    title: 'Death Note',
    summary: 'A clash of minds and moral edges.',
    year: 2006,
    season: null,
    genres: ['Mystery', 'Thriller'],
    cover_url:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuBozIXy1VC3nMuKyX0NqI3T-upZ3wXzeNsgmFVaz-2TscVq6ZLEehgH50XlDcMn3lp-JCuX2KqHNQKcEFUgEr_Qav0GbG9hLHaXeKCDKORBteGFs79FET58HqcJOA-7I3jheoY_RZYzLRspJ5mKyE8WA_gtKL-zL2vbM4dCz8lAb2SjKnWkX14_uhGRLrz3LSIocd5ITSLiZfs1o_jmE8K66308N0yG1f7_KFraWN9_PwC2foJLgTG4JlHVOA-T1MzwAr_PvRI97GI',
  },
  {
    id: 112,
    title: 'Beyond the Boundary',
    summary: 'A destined encounter between worlds.',
    year: 2013,
    season: null,
    genres: ['Battle', 'Romance'],
    cover_url:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuD-Ll4B-Sww8wiRhuAHweyWRE_q0Zh5V27d5lrKr1I5TprD6P3xTKVN4moSxovvzW1wmyyiRafygCcw70R7uXCzanS7wNWCioYPi81eH1PJbkK2UBc65-NIaQcF11s-EDjzn81w3_N8rTvID8qN8_mc18I5pX6D4egKQkjTUMmo_lyX8HeRyv8hGYtKB55bpckzFa8GKVdTH9gn6Vbxiw8Nyu1N-RolXrlodEeMdG2ER7nUElSmt6AfJIM-eGuCQGmObBds80X7dLg',
  },
]

export const mockCollections: CollectionItem[] = [
  ...buildCollectionGroup(1, 'completed', [101, 102, 103, 104, 105]),
  ...buildCollectionGroup(1, 'watching', [106, 107, 108]),
  ...buildCollectionGroup(1, 'plan_to_watch', [109, 110, 111]),
  ...buildCollectionGroup(2, 'completed', [104, 103, 105]),
  ...buildCollectionGroup(2, 'watching', [101, 106, 107]),
  ...buildCollectionGroup(2, 'plan_to_watch', [109, 111, 110]),
]

export const mockFavorites: FavoriteRankItem[] = [
  buildFavorite(1, 1, 112),
  buildFavorite(1, 2, 102),
  buildFavorite(1, 3, 105),
  buildFavorite(1, 4, 110),
  buildFavorite(2, 1, 104),
  buildFavorite(2, 2, 101),
  buildFavorite(2, 3, 103),
]

export function paginate<T>(
  source: T[],
  page = 1,
  pageSize = 20,
): ListResponse<T> {
  const safePage = Math.max(1, page)
  const safeSize = Math.max(1, pageSize)
  const start = (safePage - 1) * safeSize
  const end = start + safeSize
  return {
    items: source.slice(start, end),
    total: source.length,
    page: safePage,
    page_size: safeSize,
  }
}

function buildCollectionGroup(
  userId: number,
  status: CollectionStatus,
  animeIds: number[],
): CollectionItem[] {
  return animeIds
    .map((animeId, index) => {
      const anime = mockAnimePool.find((item) => item.id === animeId)
      if (!anime) {
        return null
      }
      return {
        id: Number(`${userId}${status.length}${index + 1}${anime.id}`),
        user_id: userId,
        anime,
        collection_status: status,
        added_at: nowIso,
        updated_at: nowIso,
      } satisfies CollectionItem
    })
    .filter((item): item is CollectionItem => item !== null)
}

function buildFavorite(userId: number, rankOrder: number, animeId: number): FavoriteRankItem {
  const anime = mockAnimePool.find((item) => item.id === animeId)
  if (!anime) {
    throw new Error(`mock anime not found for id=${animeId}`)
  }
  return {
    id: Number(`${userId}${rankOrder}${anime.id}`),
    user_id: userId,
    anime,
    rank_order: rankOrder,
    created_at: nowIso,
    updated_at: nowIso,
  }
}
